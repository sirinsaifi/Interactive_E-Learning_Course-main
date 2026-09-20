"""Course-completion certificate service.

A learner becomes eligible for a certificate once they have:
  * marked every video in the course as completed,
  * passed (at any point) every quiz attached to a section of the course, AND
  * completed every interactive activity attached to any section.

PDF is generated on demand from reportlab — no files are written to disk,
and no rows are persisted to the database. The certificate's "completion
date" is the latest of the relevant completion timestamps so it reflects
when the learner actually finished, not when they downloaded it.
"""
from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.activity import ActivityCompletion
from app.models.course import Course
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.quiz_repository import QuizRepository


@dataclass(frozen=True)
class CertificateEligibility:
    eligible: bool
    total_videos: int
    completed_videos: int
    total_quizzes: int
    passed_quizzes: int
    total_activities: int
    completed_activities: int
    completion_date: Optional[datetime]
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "total_videos": self.total_videos,
            "completed_videos": self.completed_videos,
            "total_quizzes": self.total_quizzes,
            "passed_quizzes": self.passed_quizzes,
            "total_activities": self.total_activities,
            "completed_activities": self.completed_activities,
            "completion_date": (
                self.completion_date.isoformat() if self.completion_date else None
            ),
            "reason": self.reason,
        }


class CertificateService:
    def __init__(self, db: Session):
        self.db = db
        self.course_repo = CourseRepository(db)
        self.progress_repo = ProgressRepository(db)
        self.quiz_repo = QuizRepository(db)

    # ---- Eligibility ----

    def get_eligibility(self, *, user: User, course_id: int) -> CertificateEligibility:
        course = self.course_repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")

        videos = [v for section in course.sections for v in section.videos]
        quizzes = [section.quiz for section in course.sections if section.quiz is not None]
        activities = [
            a for section in course.sections for a in (section.activities or [])
        ]

        total_videos = len(videos)
        total_quizzes = len(quizzes)
        total_activities = len(activities)

        if total_videos == 0:
            return CertificateEligibility(
                eligible=False,
                total_videos=0,
                completed_videos=0,
                total_quizzes=total_quizzes,
                passed_quizzes=0,
                total_activities=total_activities,
                completed_activities=0,
                completion_date=None,
                reason="Course has no videos yet.",
            )

        progress_rows = self.progress_repo.list_for_videos(
            user.id, [v.id for v in videos]
        )
        completed_rows = [row for row in progress_rows if row.completed]
        completed_videos = len(completed_rows)

        passed_attempts = []
        for quiz in quizzes:
            attempt = self.quiz_repo.best_attempt(user_id=user.id, quiz_id=quiz.id)
            if attempt is not None and attempt.passed:
                passed_attempts.append(attempt)
        passed_quizzes = len(passed_attempts)

        activity_completion_rows: list[ActivityCompletion] = []
        if activities:
            activity_ids = [a.id for a in activities]
            activity_completion_rows = list(
                self.db.execute(
                    select(ActivityCompletion).where(
                        ActivityCompletion.user_id == user.id,
                        ActivityCompletion.activity_id.in_(activity_ids),
                    )
                ).scalars().all()
            )
        completed_activities = len(activity_completion_rows)

        videos_done = completed_videos == total_videos
        quizzes_done = passed_quizzes == total_quizzes
        activities_done = completed_activities == total_activities

        if not (videos_done and quizzes_done and activities_done):
            reasons = []
            if not videos_done:
                reasons.append(
                    f"{total_videos - completed_videos} video(s) still to finish"
                )
            if not quizzes_done:
                reasons.append(
                    f"{total_quizzes - passed_quizzes} quiz(zes) still to pass"
                )
            if not activities_done:
                reasons.append(
                    f"{total_activities - completed_activities} activity(ies) still to complete"
                )
            return CertificateEligibility(
                eligible=False,
                total_videos=total_videos,
                completed_videos=completed_videos,
                total_quizzes=total_quizzes,
                passed_quizzes=passed_quizzes,
                total_activities=total_activities,
                completed_activities=completed_activities,
                completion_date=None,
                reason="; ".join(reasons),
            )

        # Eligible — completion date is the latest meaningful timestamp.
        timestamps: list[datetime] = []
        for row in completed_rows:
            if row.completed_at is not None:
                timestamps.append(row.completed_at)
        for attempt in passed_attempts:
            if attempt.taken_at is not None:
                timestamps.append(attempt.taken_at)
        for ac in activity_completion_rows:
            if ac.completed_at is not None:
                timestamps.append(ac.completed_at)
        completion_date = max(timestamps) if timestamps else datetime.utcnow()

        return CertificateEligibility(
            eligible=True,
            total_videos=total_videos,
            completed_videos=completed_videos,
            total_quizzes=total_quizzes,
            passed_quizzes=passed_quizzes,
            total_activities=total_activities,
            completed_activities=completed_activities,
            completion_date=completion_date,
            reason=None,
        )

    # ---- PDF generation ----

    def build_pdf(self, *, user: User, course_id: int) -> tuple[bytes, str, datetime]:
        """Return (pdf_bytes, filename, completion_date). Raises ValidationError
        when the user isn't eligible yet."""
        eligibility = self.get_eligibility(user=user, course_id=course_id)
        if not eligibility.eligible:
            raise ValidationError(
                eligibility.reason or "Course not completed yet."
            )

        course = self.course_repo.get_with_content(course_id)
        # ``get_with_content`` already returned non-None above, but appease type-checkers.
        assert course is not None

        learner_name = (user.name or user.email or "Learner").strip()
        instructor_name = _resolve_instructor_name(course)
        completion_date = eligibility.completion_date or datetime.utcnow()
        certificate_id = _make_certificate_id(
            user_id=user.id,
            course_id=course_id,
            completion_date=completion_date,
        )

        pdf_bytes = _render_certificate_pdf(
            learner_name=learner_name,
            course_title=course.title,
            instructor_name=instructor_name,
            completion_date=completion_date,
            certificate_id=certificate_id,
        )
        filename = _safe_filename(
            f"{course.slug or 'course'}-certificate-{learner_name}.pdf"
        )
        return pdf_bytes, filename, completion_date


# ---- Helpers ----------------------------------------------------------------


def _resolve_instructor_name(course: Course) -> str:
    if course.instructor_user is not None:
        name = (course.instructor_user.name or course.instructor_user.email or "").strip()
        if name:
            return name
    if course.instructor:
        return course.instructor.strip()
    return "Course Instructor"


def _safe_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in ("-", "_", ".") else "-" for c in name)
    return safe.strip("-") or "certificate.pdf"


def _make_certificate_id(*, user_id: int, course_id: int, completion_date: datetime) -> str:
    """Deterministic, human-friendly certificate identifier.

    Format: ``LS-YYYY-CCCCCC-UUUUUU-HHHHHH`` where the trailing 6-char hash is
    derived from (user_id, course_id, completion_date) so re-downloading the
    same certificate always yields the same ID, but the ID cannot be forged
    without knowing the exact completion timestamp.
    """
    payload = f"{user_id}:{course_id}:{completion_date.isoformat(timespec='seconds')}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:6].upper()
    return (
        f"LS-{completion_date.year:04d}-"
        f"{course_id:06d}-{user_id:06d}-{digest}"
    )


def _render_certificate_pdf(
    *,
    learner_name: str,
    course_title: str,
    instructor_name: str,
    completion_date: datetime,
    certificate_id: str,
) -> bytes:
    buf = io.BytesIO()
    page_size = landscape(letter)
    page_w, page_h = page_size
    c = canvas.Canvas(buf, pagesize=page_size)
    c.setTitle(f"LearnSphere Certificate — {learner_name}")
    c.setAuthor("LearnSphere")
    c.setSubject(course_title)

    # ---- Palette ----
    navy = colors.HexColor("#0f2a4a")
    navy_soft = colors.HexColor("#1f3a5f")
    gold = colors.HexColor("#c9a227")
    gold_light = colors.HexColor("#e6c76a")
    cream = colors.HexColor("#fbf7ef")
    text = colors.HexColor("#1f2937")
    muted = colors.HexColor("#6b7280")

    # ---- Background wash ----
    c.setFillColor(cream)
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    # ---- Concentric borders ----
    c.setStrokeColor(navy)
    c.setLineWidth(6)
    c.rect(0.35 * inch, 0.35 * inch, page_w - 0.7 * inch, page_h - 0.7 * inch)

    c.setStrokeColor(gold)
    c.setLineWidth(1.6)
    c.rect(0.5 * inch, 0.5 * inch, page_w - 1.0 * inch, page_h - 1.0 * inch)

    c.setStrokeColor(navy_soft)
    c.setLineWidth(0.4)
    c.rect(0.58 * inch, 0.58 * inch, page_w - 1.16 * inch, page_h - 1.16 * inch)

    # ---- Corner ornaments ----
    _draw_corner_ornaments(c, page_w, page_h, gold, navy)

    center_x = page_w / 2.0

    # ---- Header block ----
    # Small monogram bar above the wordmark.
    c.setFillColor(gold)
    c.rect(center_x - 0.4 * inch, page_h - 1.05 * inch, 0.8 * inch, 0.04 * inch, stroke=0, fill=1)

    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(center_x, page_h - 1.35 * inch, "L E A R N S P H E R E")

    c.setFillColor(muted)
    c.setFont("Helvetica", 9)
    c.drawCentredString(center_x, page_h - 1.55 * inch, "ONLINE LEARNING PLATFORM")

    # ---- Title ----
    c.setFillColor(navy)
    c.setFont("Times-Bold", 40)
    c.drawCentredString(center_x, page_h - 2.15 * inch, "Certificate of Completion")

    # Ornamental divider under the title.
    _draw_divider(c, center_x, page_h - 2.35 * inch, width=3.4 * inch, color=gold)

    c.setFillColor(muted)
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(
        center_x, page_h - 2.65 * inch, "This certificate is proudly presented to"
    )

    # ---- Learner name ----
    c.setFillColor(navy)
    name_size = _fit_font_size(c, learner_name, "Times-BoldItalic", 40, page_w - 3.5 * inch, min_size=20)
    c.setFont("Times-BoldItalic", name_size)
    c.drawCentredString(center_x, page_h - 3.35 * inch, learner_name)

    # Underline / flourish beneath the name.
    name_width = c.stringWidth(learner_name, "Times-BoldItalic", name_size)
    underline_span = max(name_width, 3.5 * inch) + 0.6 * inch
    _draw_divider(
        c,
        center_x,
        page_h - 3.55 * inch,
        width=underline_span,
        color=gold,
    )

    # ---- Recognition ----
    c.setFillColor(text)
    c.setFont("Helvetica", 12)
    c.drawCentredString(
        center_x,
        page_h - 3.95 * inch,
        "for successfully completing all videos, quizzes, and interactive activities in the course",
    )

    c.setFillColor(navy)
    course_size = _fit_font_size(c, course_title, "Times-Bold", 26, page_w - 3.0 * inch, min_size=14)
    c.setFont("Times-Bold", course_size)
    c.drawCentredString(center_x, page_h - 4.55 * inch, f"\u201c{course_title}\u201d")

    # ---- Gold seal (bottom center) ----
    seal_cx = center_x
    seal_cy = 2.55 * inch
    _draw_seal(c, seal_cx, seal_cy, navy=navy, gold=gold, gold_light=gold_light, cream=cream)

    # ---- Signature blocks (left = date, right = instructor) ----
    footer_y = 1.35 * inch
    line_y = footer_y + 0.5 * inch
    left_x = 2.2 * inch
    right_x = page_w - 2.2 * inch

    c.setStrokeColor(navy_soft)
    c.setLineWidth(0.9)
    c.line(left_x - 1.3 * inch, line_y, left_x + 1.3 * inch, line_y)
    c.line(right_x - 1.6 * inch, line_y, right_x + 1.6 * inch, line_y)

    # Signature-style script above the date line.
    c.setFillColor(navy)
    c.setFont("Times-Italic", 14)
    c.drawCentredString(left_x, line_y + 0.08 * inch, completion_date.strftime("%B %d, %Y"))
    c.drawCentredString(right_x, line_y + 0.08 * inch, instructor_name)

    c.setFillColor(muted)
    c.setFont("Helvetica", 9)
    c.drawCentredString(left_x, footer_y + 0.2 * inch, "DATE OF COMPLETION")
    c.drawCentredString(right_x, footer_y + 0.2 * inch, "COURSE INSTRUCTOR")

    # ---- Certificate ID (bottom center, under the seal) ----
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(center_x, 0.78 * inch, "CERTIFICATE ID")
    c.setFillColor(text)
    c.setFont("Courier-Bold", 11)
    c.drawCentredString(center_x, 0.6 * inch, certificate_id)

    # ---- Verification note ----
    c.setFillColor(muted)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawCentredString(
        center_x,
        0.42 * inch,
        f"Verify at learnsphere \u2014 issued on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.",
    )

    c.showPage()
    c.save()
    return buf.getvalue()


def _draw_divider(c: canvas.Canvas, cx: float, y: float, *, width: float, color: colors.Color) -> None:
    """Thin gold rule with a small diamond in the centre."""
    half = width / 2.0
    c.setStrokeColor(color)
    c.setLineWidth(0.9)
    c.line(cx - half, y, cx - 0.12 * inch, y)
    c.line(cx + 0.12 * inch, y, cx + half, y)

    # Diamond at the centre.
    c.setFillColor(color)
    d = 0.06 * inch
    p = c.beginPath()
    p.moveTo(cx, y + d)
    p.lineTo(cx + d, y)
    p.lineTo(cx, y - d)
    p.lineTo(cx - d, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def _draw_corner_ornaments(
    c: canvas.Canvas,
    page_w: float,
    page_h: float,
    gold: colors.Color,
    navy: colors.Color,
) -> None:
    """Small L-shaped flourishes tucked into each inner corner."""
    inset = 0.75 * inch
    arm = 0.55 * inch
    c.setStrokeColor(gold)
    c.setLineWidth(1.0)

    corners = [
        (inset, inset, 1, 1),                       # bottom-left
        (page_w - inset, inset, -1, 1),             # bottom-right
        (inset, page_h - inset, 1, -1),             # top-left
        (page_w - inset, page_h - inset, -1, -1),   # top-right
    ]
    for x, y, sx, sy in corners:
        c.line(x, y, x + sx * arm, y)
        c.line(x, y, x, y + sy * arm)
        # Inner accent dot in navy.
        c.setFillColor(navy)
        c.circle(x + sx * 0.09 * inch, y + sy * 0.09 * inch, 0.04 * inch, stroke=0, fill=1)


def _draw_seal(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    *,
    navy: colors.Color,
    gold: colors.Color,
    gold_light: colors.Color,
    cream: colors.Color,
) -> None:
    """Circular gold medallion with ribbon tails — mimics a wax/foil seal."""
    outer_r = 0.75 * inch
    mid_r = 0.63 * inch
    inner_r = 0.48 * inch
    core_r = 0.36 * inch

    # ---- Ribbon tails (behind the seal) ----
    c.setFillColor(navy)
    ribbon_top = cy - 0.15 * inch
    ribbon_bot = cy - 0.75 * inch
    # Left tail (parallelogram + notch).
    p = c.beginPath()
    p.moveTo(cx - 0.42 * inch, ribbon_top)
    p.lineTo(cx - 0.08 * inch, ribbon_top)
    p.lineTo(cx - 0.22 * inch, ribbon_bot)
    p.lineTo(cx - 0.46 * inch, ribbon_bot + 0.14 * inch)
    p.lineTo(cx - 0.58 * inch, ribbon_bot)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # Right tail (mirrored).
    p = c.beginPath()
    p.moveTo(cx + 0.42 * inch, ribbon_top)
    p.lineTo(cx + 0.08 * inch, ribbon_top)
    p.lineTo(cx + 0.22 * inch, ribbon_bot)
    p.lineTo(cx + 0.46 * inch, ribbon_bot + 0.14 * inch)
    p.lineTo(cx + 0.58 * inch, ribbon_bot)
    p.close()
    c.drawPath(p, stroke=0, fill=1)

    # Ribbon highlight strips.
    c.setFillColor(gold)
    c.rect(cx - 0.52 * inch, ribbon_bot + 0.02 * inch, 0.035 * inch, 0.58 * inch, stroke=0, fill=1)
    c.rect(cx + 0.485 * inch, ribbon_bot + 0.02 * inch, 0.035 * inch, 0.58 * inch, stroke=0, fill=1)

    # ---- Outer starburst points ----
    c.setFillColor(gold_light)
    points = 24
    for i in range(points):
        angle = (2 * math.pi * i) / points
        x1 = cx + math.cos(angle) * mid_r
        y1 = cy + math.sin(angle) * mid_r
        x2 = cx + math.cos(angle) * (outer_r + 0.02 * inch)
        y2 = cy + math.sin(angle) * (outer_r + 0.02 * inch)
        # Slim triangular spike.
        perp = angle + math.pi / 2
        off = 0.03 * inch
        p = c.beginPath()
        p.moveTo(x1 + math.cos(perp) * off, y1 + math.sin(perp) * off)
        p.lineTo(x1 - math.cos(perp) * off, y1 - math.sin(perp) * off)
        p.lineTo(x2, y2)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    # ---- Medallion rings ----
    c.setFillColor(gold)
    c.circle(cx, cy, mid_r, stroke=0, fill=1)

    c.setFillColor(navy)
    c.circle(cx, cy, inner_r, stroke=0, fill=1)

    c.setFillColor(gold)
    c.setStrokeColor(gold_light)
    c.setLineWidth(1.2)
    c.circle(cx, cy, core_r, stroke=1, fill=1)

    # Inner engraved circle.
    c.setStrokeColor(navy)
    c.setLineWidth(0.6)
    c.circle(cx, cy, core_r - 0.05 * inch, stroke=1, fill=0)

    # ---- Centre emblem ----
    # Small star at the very centre.
    _draw_star(c, cx, cy + 0.05 * inch, r_outer=0.13 * inch, r_inner=0.055 * inch, color=navy)

    # Wordmark arched above/below would be complex — use straight lines instead.
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(cx, cy - 0.13 * inch, "CERTIFIED")
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(cx, cy - 0.22 * inch, "\u2605 LEARNSPHERE \u2605")


def _draw_star(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    *,
    r_outer: float,
    r_inner: float,
    color: colors.Color,
) -> None:
    """Five-pointed star."""
    c.setFillColor(color)
    p = c.beginPath()
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.pi / 2 + i * math.pi / 5
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def _fit_font_size(
    c: canvas.Canvas,
    text: str,
    font: str,
    max_size: int,
    max_width: float,
    *,
    min_size: int = 12,
) -> int:
    """Shrink the font size until the text fits within max_width."""
    size = max_size
    while size > min_size and c.stringWidth(text, font, size) > max_width:
        size -= 1
    return size
