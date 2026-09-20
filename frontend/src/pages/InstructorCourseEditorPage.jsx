import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import SectionActivitiesEditor from "../components/activities/SectionActivitiesEditor.jsx";
import Spinner from "../components/Spinner.jsx";
import { instructorService } from "../services/instructorService.js";

export default function InstructorCourseEditorPage() {
  const { id } = useParams();
  const courseId = Number(id);
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingMeta, setSavingMeta] = useState(false);
  const [meta, setMeta] = useState({ title: "", description: "", instructor: "" });
  const [newSectionTitle, setNewSectionTitle] = useState("");
  const [addingSection, setAddingSection] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await instructorService.getCourse(courseId);
      setCourse(data);
      setMeta({
        title: data.title || "",
        description: data.description || "",
        instructor: data.instructor || "",
      });
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load course."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    if (Number.isFinite(courseId)) refresh();
  }, [courseId, refresh]);

  const handleSaveMeta = async () => {
    setSavingMeta(true);
    setError(null);
    try {
      const updated = await instructorService.updateCourse(courseId, {
        title: meta.title.trim(),
        description: meta.description,
        instructor: meta.instructor || null,
      });
      setCourse(updated);
      setToast("Course saved successfully.");
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to update course."
      );
    } finally {
      setSavingMeta(false);
    }
  };

  const handleDeleteCourse = async () => {
    if (
      !window.confirm(
        "Delete this course and all of its sections, videos, and quizzes? This cannot be undone."
      )
    )
      return;
    try {
      await instructorService.deleteCourse(courseId);
      navigate("/instructor");
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to delete course."
      );
    }
  };

  const handleAddSection = async (e) => {
    e.preventDefault();
    if (!newSectionTitle.trim()) return;
    setAddingSection(true);
    try {
      await instructorService.addSection(courseId, {
        title: newSectionTitle.trim(),
      });
      setNewSectionTitle("");
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to add section."
      );
    } finally {
      setAddingSection(false);
    }
  };

  if (loading) {
    return (
      <div className="py-12">
        <Spinner label="Loading course editor…" />
      </div>
    );
  }

  if (error && !course) {
    return (
      <div className="space-y-3">
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
          {error}
        </div>
        <Link
          to="/instructor"
          className="text-sm font-medium text-brand-700 hover:text-brand-600"
        >
          ← Back to my courses
        </Link>
      </div>
    );
  }

  if (!course) return null;

  return (
    <section className="space-y-8">
      <div className="flex items-center gap-2 text-sm text-fg-subtle">
        <Link to="/instructor" className="hover:text-fg">
          My courses
        </Link>
        <span className="text-line-strong">/</span>
        <span className="truncate text-fg">{course.title}</span>
      </div>

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
          {error}
        </div>
      )}

      {toast && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full border border-success/40 bg-success-soft px-4 py-2 text-sm font-medium text-success-soft-fg shadow-[var(--shadow-card)]"
        >
          <span aria-hidden="true">✓</span>
          {toast}
        </div>
      )}

      {/* Course metadata */}
      <div className="rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
        <h2 className="text-sm font-semibold text-fg">Course details</h2>
        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
              Title
            </label>
            <input
              type="text"
              value={meta.title}
              onChange={(e) => setMeta({ ...meta, title: e.target.value })}
              className="mt-1 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
              Instructor (display name)
            </label>
            <input
              type="text"
              value={meta.instructor}
              onChange={(e) =>
                setMeta({ ...meta, instructor: e.target.value })
              }
              className="mt-1 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
              Description
            </label>
            <textarea
              rows={3}
              value={meta.description}
              onChange={(e) =>
                setMeta({ ...meta, description: e.target.value })
              }
              className="mt-1 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              type="button"
              onClick={handleDeleteCourse}
              className="rounded-full border border-danger/40 bg-danger-soft px-3 py-1.5 text-xs font-medium text-danger-soft-fg transition hover:border-danger/60"
            >
              Delete course
            </button>
            <button
              type="button"
              onClick={handleSaveMeta}
              disabled={savingMeta}
              className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
            >
              {savingMeta ? "Saving…" : "Save changes"}
            </button>
          </div>
        </div>
      </div>

      {/* Sections list */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-fg">Sections</h2>
            <p className="text-xs text-fg-subtle">
              Each section gets a 4-question quiz that learners can take after the videos.
            </p>
          </div>
          <form onSubmit={handleAddSection} className="flex items-center gap-2">
            <input
              id="new-section-title"
              type="text"
              value={newSectionTitle}
              onChange={(e) => setNewSectionTitle(e.target.value)}
              placeholder="New section title"
              className="rounded-full border border-line bg-elevated px-3 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={addingSection || !newSectionTitle.trim()}
              title={
                !newSectionTitle.trim()
                  ? "Type a section title first"
                  : "Add this section"
              }
              className="rounded-full bg-brand-600 px-3 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {addingSection ? "Adding…" : "+ Add"}
            </button>
          </form>
        </div>

        {(course.sections || []).length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line bg-surface p-6 text-center">
            <p className="text-sm font-medium text-fg">No sections yet.</p>
            <p className="mt-1 text-xs text-fg-subtle">
              Give your first section a title (for example, “Introduction”) and
              click + Add to create it.
            </p>
            <form
              onSubmit={handleAddSection}
              className="mt-4 flex flex-wrap items-center justify-center gap-2"
            >
              <input
                type="text"
                autoFocus
                value={newSectionTitle}
                onChange={(e) => setNewSectionTitle(e.target.value)}
                placeholder="e.g. Introduction"
                className="w-64 rounded-full border border-line bg-elevated px-3 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={addingSection || !newSectionTitle.trim()}
                className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {addingSection ? "Adding…" : "+ Add section"}
              </button>
            </form>
          </div>
        ) : (
          course.sections.map((section) => (
            <SectionEditor
              key={section.id}
              section={section}
              onChanged={refresh}
              onError={setError}
            />
          ))
        )}
      </div>
    </section>
  );
}

function SectionEditor({ section, onChanged, onError }) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [title, setTitle] = useState(section.title);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [editingQuiz, setEditingQuiz] = useState(false);
  const [editingActivities, setEditingActivities] = useState(false);
  const fileRef = useRef(null);

  const saveTitle = async () => {
    if (title.trim() === section.title) {
      setEditingTitle(false);
      return;
    }
    try {
      await instructorService.updateSection(section.id, { title: title.trim() });
      setEditingTitle(false);
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to rename section."
      );
    }
  };

  const handleDeleteSection = async () => {
    if (
      !window.confirm(
        `Delete section “${section.title}” along with its videos and quiz?`
      )
    )
      return;
    try {
      await instructorService.deleteSection(section.id);
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to delete section."
      );
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-uploading same file later
    if (!file) return;
    setUploading(true);
    setProgress(0);
    try {
      await instructorService.uploadVideo(section.id, file, {
        title: file.name.replace(/\.[^.]+$/, ""),
        onProgress: setProgress,
      });
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to upload video."
      );
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
        {editingTitle ? (
          <div className="flex flex-1 items-center gap-2">
            <input
              autoFocus
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="flex-1 rounded-lg border border-line bg-elevated px-3 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={saveTitle}
              className="rounded-full bg-brand-600 px-3 py-1 text-xs font-medium text-brand-fg hover:bg-brand-700"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => {
                setTitle(section.title);
                setEditingTitle(false);
              }}
              className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold text-fg">{section.title}</h3>
            <button
              type="button"
              onClick={() => setEditingTitle(true)}
              className="text-xs font-medium text-brand-700 hover:text-brand-600"
            >
              Rename
            </button>
          </div>
        )}
        <div className="flex items-center gap-2">
          {section.quiz && (
            <button
              type="button"
              onClick={() => setEditingQuiz((v) => !v)}
              className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
            >
              {editingQuiz ? "Hide quiz" : "Edit quiz"}
            </button>
          )}
          <button
            type="button"
            onClick={() => setEditingActivities((v) => !v)}
            className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
          >
            {editingActivities ? "Hide activities" : "Activities"}
          </button>
          <button
            type="button"
            onClick={handleDeleteSection}
            className="rounded-full border border-danger/40 bg-danger-soft px-3 py-1 text-xs font-medium text-danger-soft-fg transition hover:border-danger/60"
          >
            Delete
          </button>
        </div>
      </header>

      <div className="divide-y divide-line">
        {(section.videos || []).map((video) => (
          <VideoRow
            key={video.id}
            video={video}
            onChanged={onChanged}
            onError={onError}
          />
        ))}
        {(section.videos || []).length === 0 && (
          <div className="px-5 py-4 text-sm text-fg-subtle">
            No videos in this section yet.
          </div>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-line px-5 py-3">
        <div className="flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov,.mkv,.m4v"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="rounded-full bg-brand-600 px-3 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
          >
            {uploading ? `Uploading… ${progress}%` : "+ Upload video"}
          </button>
        </div>
        {uploading && (
          <div className="ml-3 h-1.5 w-40 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-brand-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {editingQuiz && section.quiz && (
        <QuizEditor quizId={section.quiz.id} onError={onError} />
      )}

      {editingActivities && (
        <SectionActivitiesEditor sectionId={section.id} onError={onError} />
      )}
    </div>
  );
}

function VideoRow({ video, onChanged, onError }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    title: video.title,
    description: video.description || "",
  });

  const save = async () => {
    try {
      await instructorService.updateVideo(video.id, {
        title: form.title.trim(),
        description: form.description,
      });
      setEditing(false);
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to update video."
      );
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete video “${video.title}”?`)) return;
    try {
      await instructorService.deleteVideo(video.id);
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to delete video."
      );
    }
  };

  if (editing) {
    return (
      <div className="space-y-2 px-5 py-3">
        <input
          type="text"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          className="w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
        />
        <textarea
          rows={2}
          placeholder="Description (optional)"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
        />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setEditing(false)}
            className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={save}
            className="rounded-full bg-brand-600 px-3 py-1 text-xs font-medium text-brand-fg hover:bg-brand-700"
          >
            Save
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-2 px-5 py-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-fg">{video.title}</p>
        {video.description && (
          <p className="truncate text-xs text-fg-subtle">{video.description}</p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg hover:border-line-strong"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={remove}
          className="rounded-full border border-danger/40 bg-danger-soft px-3 py-1 text-xs font-medium text-danger-soft-fg hover:border-danger/60"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

function QuizEditor({ quizId, onError }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setQuiz(await instructorService.getQuizForEdit(quizId));
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load quiz."
      );
    } finally {
      setLoading(false);
    }
  }, [quizId, onError]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="border-t border-line px-5 py-5">
        <Spinner label="Loading quiz…" />
      </div>
    );
  }

  if (!quiz) return null;

  return (
    <div className="space-y-4 border-t border-line bg-elevated/40 px-5 py-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
          Section quiz
        </p>
        <p className="text-xs text-fg-subtle">
          Update the 4 placeholder questions with your real content. Pick the
          correct option for each.
        </p>
      </div>
      <ol className="space-y-3">
        {[...quiz.questions]
          .sort((a, b) => a.position - b.position)
          .map((q, idx) => (
            <QuestionEditor
              key={q.id}
              quizId={quiz.id}
              question={q}
              index={idx}
              onChanged={load}
              onError={onError}
            />
          ))}
      </ol>
    </div>
  );
}

function QuestionEditor({ quizId, question, index, onChanged, onError }) {
  const [text, setText] = useState(question.text);
  const [options, setOptions] = useState(question.options);
  const [correctIndex, setCorrectIndex] = useState(question.correct_index);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const handleOption = (i, val) => {
    const next = [...options];
    next[i] = val;
    setOptions(next);
    setDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await instructorService.updateQuestion(quizId, question.id, {
        text: text.trim(),
        options,
        correct_index: correctIndex,
      });
      setDirty(false);
      onChanged();
    } catch (e) {
      onError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to update question."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <li className="rounded-xl border border-line bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
          Question {index + 1}
        </p>
        {dirty && (
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-full bg-brand-600 px-3 py-1 text-xs font-medium text-brand-fg hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save question"}
          </button>
        )}
      </div>
      <textarea
        rows={2}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setDirty(true);
        }}
        className="mt-2 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
      />
      <div className="mt-3 space-y-2">
        {options.map((opt, i) => (
          <label
            key={i}
            className={`flex items-start gap-3 rounded-lg border px-3 py-2 text-sm ${
              correctIndex === i
                ? "border-success/40 bg-success-soft text-success-soft-fg"
                : "border-line bg-elevated text-fg-muted"
            }`}
          >
            <input
              type="radio"
              name={`correct-${question.id}`}
              checked={correctIndex === i}
              onChange={() => {
                setCorrectIndex(i);
                setDirty(true);
              }}
              className="mt-1 accent-brand-600"
            />
            <input
              type="text"
              value={opt}
              onChange={(e) => handleOption(i, e.target.value)}
              className="flex-1 bg-transparent text-sm text-fg outline-none"
            />
          </label>
        ))}
      </div>
    </li>
  );
}
