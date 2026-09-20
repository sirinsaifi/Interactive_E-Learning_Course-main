"""Filesystem → database sync for course content.

Scans `storage/videos/` and upserts Course / Section / Video rows so that
the catalog reflects whatever is on disk. Used by both:

  * FastAPI startup lifespan (when `AUTO_SEED_ON_STARTUP=true`)
  * The CLI helper `scripts/seed_sample_courses.py`

Two on-disk layouts are supported:

  storage/videos/<course-slug>/<NN-section>/<NN-video>.mp4   (nested)
  storage/videos/<course-slug>/<NN-video>.mp4                (flat → "Lessons")

The optional leading `NN-` (digits + separator) sets `order_index` and is
stripped from the displayed title.

Sync is **upsert by natural key** so DB ids stay stable across restarts:
  * Section is keyed by (course_id, title)
  * Video   is keyed by (section_id, file_path)
This matters because user progress rows reference video.id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.course import Course, Section, Video
from app.models.quiz import Quiz, QuizQuestion
from app.utils.storage import thumbnails_dir, videos_dir

logger = get_logger(__name__)

VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".m4v", ".html"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_SECTION_TITLE = "Lessons"

_PREFIX_RE = re.compile(r"^\d+[-_ ]+")


def _humanize(name: str) -> str:
    return _PREFIX_RE.sub("", name).replace("-", " ").replace("_", " ").strip().title() or name


def _order_index(name: str, fallback: int) -> int:
    match = re.match(r"^(\d+)", name)
    return int(match.group(1)) if match else fallback


def _find_thumbnail(slug: str) -> str | None:
    for ext in IMAGE_EXTS:
        candidate = thumbnails_dir() / f"{slug}{ext}"
        if candidate.exists():
            return candidate.name
    return None


@dataclass
class SyncStats:
    courses_added: int = 0
    courses_updated: int = 0
    courses_removed: int = 0
    sections_added: int = 0
    sections_removed: int = 0
    videos_added: int = 0
    videos_removed: int = 0
    videos_indexed: int = 0
    quizzes_added: int = 0


def sync_content(db: Session, *, prune_missing_courses: bool = False) -> SyncStats:
    """Mirror the on-disk video tree into the database."""
    root = videos_dir()
    if not root.exists():
        logger.info("Storage directory %s does not exist; skipping content sync.", root)
        return SyncStats()

    course_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    seen_slugs: set[str] = set()
    stats = SyncStats()

    for course_dir in course_dirs:
        slug = course_dir.name
        title = _humanize(slug)
        seen_slugs.add(slug)

        course = db.execute(select(Course).where(Course.slug == slug)).scalar_one_or_none()
        if course is None:
            course = Course(
                slug=slug,
                title=title,
                instructor="LearnSphere Instructor",
                description=f"Auto-synced from {slug}/",
                thumbnail_path=_find_thumbnail(slug),
            )
            db.add(course)
            db.flush()
            stats.courses_added += 1
        else:
            course.title = title
            course.thumbnail_path = _find_thumbnail(slug) or course.thumbnail_path
            stats.courses_updated += 1

        _sync_course_tree(db, course, course_dir, root, stats)

    if prune_missing_courses:
        existing = db.execute(select(Course)).scalars().all()
        for c in existing:
            if c.slug in seen_slugs:
                continue
            if c.instructor_id is not None:
                continue
            db.delete(c)
            stats.courses_removed += 1

    db.commit()
    logger.info(
        "Content sync: +%d courses, ~%d updated, -%d removed, "
        "+%d sections / -%d, +%d videos / -%d (indexed %d), +%d quizzes",
        stats.courses_added,
        stats.courses_updated,
        stats.courses_removed,
        stats.sections_added,
        stats.sections_removed,
        stats.videos_added,
        stats.videos_removed,
        stats.videos_indexed,
        stats.quizzes_added,
    )
    return stats


def _sync_course_tree(
    db: Session,
    course: Course,
    course_dir: Path,
    root: Path,
    stats: SyncStats,
) -> None:
    desired: dict[str, tuple[int, list[Path]]] = {}

    section_dirs = sorted(p for p in course_dir.iterdir() if p.is_dir())
    if section_dirs:
        for s_idx, section_dir in enumerate(section_dirs, start=1):
            videos = sorted(
                p for p in section_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS
            )
            if not videos:
                continue
            desired[_humanize(section_dir.name)] = (
                _order_index(section_dir.name, s_idx),
                videos,
            )
    else:
        videos = sorted(
            p for p in course_dir.iterdir() if p.suffix.lower() in VIDEO_EXTS
        )
        if videos:
            desired[DEFAULT_SECTION_TITLE] = (1, videos)

    existing_sections = {s.title: s for s in course.sections}

    for stale_title in set(existing_sections) - set(desired):
        db.delete(existing_sections[stale_title])
        stats.sections_removed += 1
    db.flush()

    for sec_title, (sec_order, files) in desired.items():
        section = existing_sections.get(sec_title)
        if section is None:
            section = Section(
                course_id=course.id,
                title=sec_title,
                order_index=sec_order,
            )
            db.add(section)
            db.flush()
            stats.sections_added += 1
        else:
            section.order_index = sec_order

        _sync_section_videos(db, section, files, root, stats)
        stats.videos_indexed += len(files)
        _ensure_section_quiz(db, section, stats)


def _sync_section_videos(
    db: Session,
    section: Section,
    files: list[Path],
    root: Path,
    stats: SyncStats,
) -> None:
    desired_paths = {f.relative_to(root).as_posix(): (idx, f) for idx, f in enumerate(files, 1)}
    existing = {v.file_path: v for v in section.videos}

    for stale_path in set(existing) - set(desired_paths):
        db.delete(existing[stale_path])
        stats.videos_removed += 1
    db.flush()

    for rel, (idx, vf) in desired_paths.items():
        title = _humanize(vf.stem)
        order = _order_index(vf.stem, idx)
        video = existing.get(rel)
        if video is None:
            db.add(
                Video(
                    section_id=section.id,
                    title=title,
                    file_path=rel,
                    order_index=order,
                )
            )
            stats.videos_added += 1
        else:
            video.title = title
            video.order_index = order
    db.flush()


# ---------------------------------------------------------------------------
# Module-specific quiz questions
# Each key matches the section title produced by _humanize() from the folder name.
# 3 questions per module, 15 questions for the Final Assessment.
# ---------------------------------------------------------------------------

_MODULE_QUESTIONS: dict[str, list[dict]] = {
    "Module 1": [
        {
            "text": "What is the very first step in the drug discovery process?",
            "options": [
                "Clinical trials in patients",
                "Target identification — finding the biological molecule linked to a disease",
                "Regulatory submission to health authorities",
                "Commercial launch and marketing",
            ],
            "correct_index": 1,
        },
        {
            "text": "Which technique rapidly tests thousands of compounds against a target in parallel?",
            "options": [
                "Manual titration",
                "Patient observation studies",
                "High-throughput screening (HTS)",
                "MRI scanning",
            ],
            "correct_index": 2,
        },
        {
            "text": "Approximately how many years does the full drug discovery and development cycle typically take?",
            "options": [
                "1–2 years",
                "3–6 years",
                "10–15 years",
                "25–30 years",
            ],
            "correct_index": 2,
        },
    ],
    "Module 2": [
        {
            "text": "Drug discovery is often compared to a relay race because:",
            "options": [
                "It has a fixed time limit of one hour",
                "Multiple specialist teams hand off work to each other across sequential stages",
                "One scientist carries the entire project from start to finish",
                "Speed is the only factor that matters",
            ],
            "correct_index": 1,
        },
        {
            "text": "How many broad stages does a typical drug discovery and development programme progress through?",
            "options": [
                "2",
                "4",
                "6",
                "12",
            ],
            "correct_index": 2,
        },
        {
            "text": "Which of the following is NOT a typical specialist team involved in drug discovery?",
            "options": [
                "Medicinal chemists",
                "Toxicologists",
                "Civil engineers",
                "Pharmacologists",
            ],
            "correct_index": 2,
        },
    ],
    "Module 3": [
        {
            "text": "In the end-to-end drug discovery process, what immediately follows the 'hypothesis' stage?",
            "options": [
                "Regulatory submission",
                "Designing and running experiments to test the hypothesis",
                "Commercial launch",
                "Patent filing",
            ],
            "correct_index": 1,
        },
        {
            "text": "What does the 'evidence' stage in the end-to-end process involve?",
            "options": [
                "Advertising the drug to prescribers",
                "Collecting and analysing experimental data to support or refute the hypothesis",
                "Gathering patient reviews after launch",
                "Lobbying regulatory agencies",
            ],
            "correct_index": 1,
        },
        {
            "text": "After sufficient evidence is accumulated, what is the next critical milestone toward patient access?",
            "options": [
                "Restarting the hypothesis phase",
                "Submitting a regulatory dossier for approval",
                "Skipping directly to manufacturing scale-up",
                "Rebranding the compound for a different disease",
            ],
            "correct_index": 1,
        },
    ],
    "Module 4": [
        {
            "text": "Which document must be filed with health authorities before a compound can be tested in humans?",
            "options": [
                "A patent application",
                "An Investigational New Drug (IND) application",
                "A marketing authorisation",
                "A manufacturing site licence",
            ],
            "correct_index": 1,
        },
        {
            "text": "Phase 1 clinical trials are primarily designed to assess:",
            "options": [
                "Efficacy in a large patient population",
                "Safety and dosing in healthy volunteers",
                "Long-term side effects over decades",
                "Drug pricing strategies",
            ],
            "correct_index": 1,
        },
        {
            "text": "Phase 2 clinical trials differ from Phase 1 because they:",
            "options": [
                "Are conducted in healthy volunteers only",
                "Involve patients and begin to evaluate preliminary efficacy",
                "Are post-market surveillance studies",
                "Only use animal models",
            ],
            "correct_index": 1,
        },
    ],
    "Module 5": [
        {
            "text": "Why are patents critical to pharmaceutical companies investing in drug development?",
            "options": [
                "They prevent scientists from publishing their research",
                "They grant a period of market exclusivity that allows the company to recoup its R&D investment",
                "They eliminate the requirement for clinical trials",
                "They guarantee that regulators will approve the drug",
            ],
            "correct_index": 1,
        },
        {
            "text": "Bringing a new drug to market typically requires a financial investment of:",
            "options": [
                "A few thousand dollars",
                "Hundreds of millions of dollars",
                "Purely public funding with no private cost",
                "Costs fully covered by health insurance companies",
            ],
            "correct_index": 1,
        },
        {
            "text": "What does 'market exclusivity' mean in the context of pharmaceuticals?",
            "options": [
                "The drug can only be sold in one country",
                "A period during which generic competitors cannot legally enter the market",
                "The drug is available exclusively in hospitals",
                "Only one physician per region may prescribe the drug",
            ],
            "correct_index": 1,
        },
    ],
    "Module 6": [
        {
            "text": "What is a Laboratory Information Management System (LIMS)?",
            "options": [
                "A high-powered microscope used in drug synthesis",
                "Software that tracks laboratory samples, workflows, and data to ensure traceability and compliance",
                "A phase in clinical development",
                "A regulatory body that approves new drugs",
            ],
            "correct_index": 1,
        },
        {
            "text": "Digital lab notebooks replace paper records primarily to:",
            "options": [
                "Make laboratories look more modern",
                "Improve data integrity, searchability, version control, and regulatory compliance",
                "Reduce the number of experiments scientists need to perform",
                "Automate the chemical synthesis of drug candidates",
            ],
            "correct_index": 1,
        },
        {
            "text": "Cloud computing platforms benefit drug discovery organisations mainly by:",
            "options": [
                "Replacing the need for trained scientists",
                "Enabling scalable data storage, global collaboration, and on-demand computational power",
                "Eliminating the need for physical laboratory space entirely",
                "Automatically submitting regulatory dossiers",
            ],
            "correct_index": 1,
        },
    ],
    "Module 7": [
        {
            "text": "How is machine learning applied to genomic datasets in drug discovery?",
            "options": [
                "To design packaging artwork for approved drugs",
                "To identify patterns that link genetic variants to diseases and pinpoint new drug targets",
                "To replace Phase 3 clinical trials",
                "To train hospital pharmacists",
            ],
            "correct_index": 1,
        },
        {
            "text": "Generative AI models in drug discovery are used to:",
            "options": [
                "Conduct clinical trials without human participants",
                "Propose entirely novel molecular structures as potential drug candidates",
                "Replace national regulatory agencies",
                "Mass-produce already approved drugs",
            ],
            "correct_index": 1,
        },
        {
            "text": "The primary advantage of AI-driven approaches in drug discovery is that they can:",
            "options": [
                "Guarantee that every candidate will pass clinical trials",
                "Accelerate the identification and optimisation of drug candidates, reducing time and cost",
                "Eliminate the need for animal or human testing",
                "Remove the requirement for intellectual property protection",
            ],
            "correct_index": 1,
        },
    ],
    "Module 8": [
        {
            "text": "What are CDISC/SDTM standards used for in drug development?",
            "options": [
                "Designing drug molecules using computational chemistry",
                "Standardising the format of clinical trial data for regulatory submission and review",
                "Training laboratory animals for safety studies",
                "Managing the patent portfolio of pharmaceutical companies",
            ],
            "correct_index": 1,
        },
        {
            "text": "Which types of data are collected during preclinical studies?",
            "options": [
                "Social media sentiment about the drug",
                "Laboratory and animal study data measuring biological activity and safety profiles",
                "Stock market data for the sponsoring pharmaceutical company",
                "Patient satisfaction questionnaires",
            ],
            "correct_index": 1,
        },
        {
            "text": "Why is structured clinical data important throughout drug development?",
            "options": [
                "It makes reports more visually appealing",
                "It enables reliable analysis, cross-study comparison, and efficient regulatory review",
                "It removes the need for statistical analysis",
                "It automatically triggers drug approval",
            ],
            "correct_index": 1,
        },
    ],
    "Module 9": [
        {
            "text": "Which of the following represents one of the biggest challenges in clinical drug development?",
            "options": [
                "An overabundance of approved drugs",
                "High failure rates of candidates during clinical trials",
                "Excess public and private funding",
                "Lack of patient interest in participating in studies",
            ],
            "correct_index": 1,
        },
        {
            "text": "Rising development costs in the pharmaceutical industry are primarily driven by:",
            "options": [
                "Increasing marketing and advertising budgets",
                "Growing clinical trial complexity and increasingly stringent regulatory requirements",
                "Excessive profits reinvested inefficiently",
                "Reduced use of digital technologies",
            ],
            "correct_index": 1,
        },
        {
            "text": "Regulatory fragmentation across countries affects drug development by:",
            "options": [
                "Speeding up approval for all companies equally",
                "Creating different submission standards and timelines that companies must navigate in each market",
                "Reducing the chemical stability of drug candidates",
                "Fragmenting the global supply chain for raw materials",
            ],
            "correct_index": 1,
        },
    ],
    "Module 10": [
        {
            "text": "In the context of drug development, 'real-world evidence' refers to:",
            "options": [
                "Anecdotal reports gathered from social media platforms",
                "Data from patients in everyday clinical practice — such as electronic health records — outside controlled trials",
                "Results generated only from animal safety studies",
                "Early-stage laboratory findings",
            ],
            "correct_index": 1,
        },
        {
            "text": "Personalised or precision medicine aims to:",
            "options": [
                "Produce a single universal treatment for all patients regardless of biology",
                "Tailor treatments to individual patients based on their genetic makeup and clinical profile",
                "Reduce the total variety of available medicines",
                "Make all prescription drugs available over the counter",
            ],
            "correct_index": 1,
        },
        {
            "text": "How is AI expected to change drug discovery timelines in the future?",
            "options": [
                "It is not expected to have any significant impact",
                "By compressing timelines — accelerating target identification, candidate selection, and trial design",
                "By making drug development significantly slower due to additional complexity",
                "By removing the need for human scientific judgement entirely",
            ],
            "correct_index": 1,
        },
    ],
    "Module 11": [
        {
            "text": "Which sequence correctly describes the major phases of the full drug development pathway?",
            "options": [
                "Clinical trials → Preclinical → Discovery → Regulatory approval",
                "Discovery → Preclinical studies → Clinical Phases 1, 2 & 3 → Regulatory review → Market approval",
                "Regulatory review → Discovery → Preclinical → Clinical trials",
                "Approval → Clinical trials → Discovery → Preclinical",
            ],
            "correct_index": 1,
        },
        {
            "text": "How many distinct clinical trial phases are there in a standard drug development programme?",
            "options": [
                "1",
                "2",
                "3",
                "5",
            ],
            "correct_index": 2,
        },
        {
            "text": "Regulatory review is best described as:",
            "options": [
                "An optional step that established companies may choose to skip",
                "A mandatory evaluation by health authorities before a drug can be approved and marketed",
                "An internal audit conducted solely by the manufacturer",
                "A process required only in the United States",
            ],
            "correct_index": 1,
        },
    ],
    "Final Assessment": [
        {
            "text": "What is the very first step in the drug discovery process?",
            "options": [
                "Regulatory submission",
                "Target identification",
                "Phase 3 clinical trials",
                "Commercial launch",
            ],
            "correct_index": 1,
        },
        {
            "text": "Drug discovery is best described as a process that relies on:",
            "options": [
                "A single scientist working independently from start to finish",
                "Multiple specialist teams working in relay across sequential stages",
                "Government agencies managing all decisions",
                "Fully automated machines with no human input",
            ],
            "correct_index": 1,
        },
        {
            "text": "Which document must be filed with health authorities before a compound can be tested in humans?",
            "options": [
                "A patent application",
                "An Investigational New Drug (IND) application",
                "A commercial marketing licence",
                "A manufacturing site certificate",
            ],
            "correct_index": 1,
        },
        {
            "text": "Phase 1 clinical trials primarily involve:",
            "options": [
                "Large patient populations testing long-term efficacy",
                "Healthy volunteers assessing safety and dosing",
                "Post-market surveillance of approved drugs",
                "Animal model experiments only",
            ],
            "correct_index": 1,
        },
        {
            "text": "Patents in the pharmaceutical industry are important because they:",
            "options": [
                "Prevent scientists from publishing their research",
                "Provide a period of market exclusivity that allows recovery of R&D investment",
                "Eliminate the need for clinical trials",
                "Guarantee regulatory approval by all agencies",
            ],
            "correct_index": 1,
        },
        {
            "text": "LIMS stands for:",
            "options": [
                "Linear Integrated Medicine System",
                "Laboratory Information Management System",
                "Large-scale Imaging and Monitoring Software",
                "Licensed Investigational Medicines Standard",
            ],
            "correct_index": 1,
        },
        {
            "text": "Generative AI models are applied in drug discovery to:",
            "options": [
                "Conduct clinical trials without human participants",
                "Propose novel molecular structures as potential drug candidates",
                "Replace national regulatory agencies",
                "Mass-produce commercially approved drugs",
            ],
            "correct_index": 1,
        },
        {
            "text": "CDISC/SDTM data standards are primarily used for:",
            "options": [
                "Designing laboratory equipment",
                "Standardising clinical trial data formats for regulatory submissions",
                "Training researchers in lab techniques",
                "Automating drug manufacturing",
            ],
            "correct_index": 1,
        },
        {
            "text": "High failure rates during clinical trials are an example of:",
            "options": [
                "A successful outcome in drug development",
                "A major challenge that drives up costs and development timelines",
                "Standard regulatory approval procedure",
                "Normal and expected market behaviour with no impact on cost",
            ],
            "correct_index": 1,
        },
        {
            "text": "Real-world evidence in drug development is data collected:",
            "options": [
                "Only under tightly controlled laboratory conditions",
                "From patients in routine clinical practice, such as electronic health records",
                "Exclusively from animal preclinical studies",
                "By marketing teams after commercial launch",
            ],
            "correct_index": 1,
        },
        {
            "text": "Precision (personalised) medicine tailors treatments based on:",
            "options": [
                "The market price of the drug",
                "A patient's genetic and individual clinical profile",
                "The prescribing doctor's personal preference",
                "Drug availability in a given region",
            ],
            "correct_index": 1,
        },
        {
            "text": "The full drug discovery and approval cycle typically takes approximately:",
            "options": [
                "1–2 years",
                "3–5 years",
                "10–15 years",
                "50 or more years",
            ],
            "correct_index": 2,
        },
        {
            "text": "Regulatory fragmentation in drug development refers to:",
            "options": [
                "Chemical instability of the drug compound across regions",
                "Varying approval standards and submission requirements across different countries",
                "Internal disagreements within a single regulatory body",
                "Differences in manufacturing processes at different sites",
            ],
            "correct_index": 1,
        },
        {
            "text": "Which technology helps research organisations track lab workflows, samples, and data electronically?",
            "options": [
                "Social media management platforms",
                "Laboratory Information Management Systems (LIMS)",
                "Global Positioning System (GPS) tracking",
                "Customer Relationship Management (CRM) software",
            ],
            "correct_index": 1,
        },
        {
            "text": "Which sequence correctly describes the complete drug development pathway?",
            "options": [
                "Approval → Clinical trials → Discovery → Preclinical",
                "Discovery → Preclinical → Clinical Phases 1, 2 & 3 → Regulatory review → Market approval",
                "Preclinical → Discovery → Regulatory review → Approval",
                "Clinical trials → Patent filing → Discovery → Preclinical",
            ],
            "correct_index": 1,
        },
    ],
}

# Fallback for any section not covered above
_FALLBACK_QUESTIONS: list[dict] = [
    {
        "text": "Which of the following best describes the focus of this section?",
        "options": [
            "Hands-on practical lessons",
            "Theory and concepts",
            "Reference material only",
            "All of the above",
        ],
        "correct_index": 3,
    },
    {
        "text": "What is the most effective way to absorb new material in a video lesson?",
        "options": [
            "Watch every video in one sitting without breaks",
            "Pause, take notes, and rewatch difficult parts",
            "Skip ahead to the conclusion",
            "Only watch the introduction",
        ],
        "correct_index": 1,
    },
    {
        "text": "Why do short quizzes after a section improve long-term retention?",
        "options": [
            "They make the course longer",
            "Active recall reinforces memory",
            "They replace the need to watch videos",
            "They are required by the platform",
        ],
        "correct_index": 1,
    },
]


def _ensure_section_quiz(db: Session, section: Section, stats: SyncStats) -> None:
    """Make sure each section has a quiz seeded with module-specific questions."""
    existing = db.execute(
        select(Quiz).where(Quiz.section_id == section.id)
    ).scalar_one_or_none()
    if existing is not None:
        # Ensure pass_threshold is correct (67 = 2/3 correct for module quizzes)
        if existing.pass_threshold != 67:
            existing.pass_threshold = 67
            db.flush()
        return

    questions = _MODULE_QUESTIONS.get(section.title, _FALLBACK_QUESTIONS)

    quiz_title = (
        "Final Assessment Quiz" if section.title == "Final Assessment"
        else f"{section.title} Quiz"
    )
    quiz = Quiz(section_id=section.id, title=quiz_title, pass_threshold=67)
    db.add(quiz)
    db.flush()

    for idx, q in enumerate(questions):
        opts = q["options"]
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                position=idx,
                text=q["text"],
                option_a=opts[0],
                option_b=opts[1],
                option_c=opts[2],
                option_d=opts[3],
                correct_index=q["correct_index"],
            )
        )
    db.flush()
    stats.quizzes_added += 1
