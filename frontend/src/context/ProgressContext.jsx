import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { useAuth } from "./AuthContext.jsx";
import { progressService } from "../services/progressService.js";
import { quizService } from "../services/quizService.js";

const ProgressContext = createContext(null);

const SAVE_INTERVAL_MS = 5000; // server heartbeat cadence

function indexByVideoId(items) {
  const out = {};
  for (const p of items || []) out[p.video_id] = p;
  return out;
}

export function ProgressProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [courseId, setCourseId] = useState(null);
  const [summary, setSummary] = useState(null); // CourseProgressSummary
  const [byVideoId, setByVideoId] = useState({}); // video_id -> VideoProgressRead
  // Set of quiz IDs the current user has passed for the active course.
  const [passedQuizIds, setPassedQuizIds] = useState(new Set());

  // Throttle state for heartbeats. We persist the last sent payload to avoid
  // hammering the server when the user is paused.
  const lastSentRef = useRef({ videoId: null, position: -1, at: 0 });

  // Load progress whenever the active course changes (and we are signed in).
  const loadCourseProgress = useCallback(
    async (id) => {
      setCourseId(id);
      if (!id || !isAuthenticated) {
        setSummary(null);
        setByVideoId({});
        setPassedQuizIds(new Set());
        return null;
      }
      try {
        const [data, passedIds] = await Promise.all([
          progressService.getCourseProgress(id),
          quizService.getPassedForCourse(id).catch(() => []),
        ]);
        setSummary(data);
        setByVideoId(indexByVideoId(data?.videos));
        setPassedQuizIds(new Set(passedIds));
        return data;
      } catch {
        setSummary(null);
        setByVideoId({});
        setPassedQuizIds(new Set());
        return null;
      }
    },
    [isAuthenticated]
  );

  // Reset when the user signs out.
  useEffect(() => {
    if (!isAuthenticated) {
      setSummary(null);
      setByVideoId({});
      setPassedQuizIds(new Set());
      lastSentRef.current = { videoId: null, position: -1, at: 0 };
    }
  }, [isAuthenticated]);

  const applyServerRow = useCallback((row) => {
    if (!row?.video_id) return;
    setByVideoId((prev) => ({ ...prev, [row.video_id]: row }));
    setSummary((prev) => {
      if (!prev) return prev;
      const wasCompleted = prev.videos?.find((v) => v.video_id === row.video_id)
        ?.completed;
      const justCompleted = row.completed && !wasCompleted;
      const completed = (prev.completed_videos || 0) + (justCompleted ? 1 : 0);
      const total = prev.total_videos || 0;
      const percent = total ? Math.round((completed / total) * 100) : 0;
      const videos = prev.videos ? [...prev.videos] : [];
      const idx = videos.findIndex((v) => v.video_id === row.video_id);
      if (idx >= 0) videos[idx] = row;
      else videos.push(row);
      return {
        ...prev,
        completed_videos: completed,
        percent_complete: percent,
        last_video_id: row.video_id,
        last_position_seconds: row.position_seconds,
        videos,
      };
    });
  }, []);

  /** Called when a quiz attempt passes — optimistically marks the quiz as passed. */
  const recordQuizPass = useCallback((quizId) => {
    if (!quizId) return;
    setPassedQuizIds((prev) => {
      if (prev.has(quizId)) return prev;
      const next = new Set(prev);
      next.add(quizId);
      return next;
    });
  }, []);

  /** Called by the player on timeupdate. Throttled to once per ~5s. */
  const recordPosition = useCallback(
    (videoId, positionSeconds, durationSeconds) => {
      if (!isAuthenticated || !videoId) return;
      const now = Date.now();
      const last = lastSentRef.current;
      const movedEnough = Math.abs(positionSeconds - last.position) >= 5;
      const newVideo = last.videoId !== videoId;
      const dueByTime = now - last.at >= SAVE_INTERVAL_MS;
      if (!newVideo && !(dueByTime && movedEnough)) return;
      lastSentRef.current = { videoId, position: positionSeconds, at: now };
      progressService
        .updateVideoProgress(videoId, { positionSeconds, durationSeconds })
        .then(applyServerRow)
        .catch(() => {
          /* swallow — heartbeat will retry */
        });
    },
    [isAuthenticated, applyServerRow]
  );

  /** Called by the player on the 'ended' event. */
  const markComplete = useCallback(
    (videoId) => {
      if (!isAuthenticated || !videoId) return Promise.resolve(null);
      return progressService
        .markVideoComplete(videoId)
        .then((row) => {
          applyServerRow(row);
          return row;
        })
        .catch(() => null);
    },
    [isAuthenticated, applyServerRow]
  );

  const value = useMemo(
    () => ({
      courseId,
      summary,
      byVideoId,
      passedQuizIds,
      loadCourseProgress,
      recordPosition,
      markComplete,
      recordQuizPass,
    }),
    [courseId, summary, byVideoId, passedQuizIds, loadCourseProgress, recordPosition, markComplete, recordQuizPass]
  );

  return (
    <ProgressContext.Provider value={value}>{children}</ProgressContext.Provider>
  );
}

export function useProgress() {
  const ctx = useContext(ProgressContext);
  if (!ctx) throw new Error("useProgress must be used inside <ProgressProvider>");
  return ctx;
}
