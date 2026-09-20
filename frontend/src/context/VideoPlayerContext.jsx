import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

const VideoPlayerContext = createContext(null);

/**
 * Flatten a course's nested sections → videos into a single ordered playlist.
 */
function buildPlaylist(course) {
  if (!course?.sections) return [];
  const items = [];
  for (const section of course.sections) {
    for (const video of section.videos || []) {
      items.push({
        ...video,
        sectionId: section.id,
        sectionTitle: section.title,
      });
    }
  }
  return items;
}

export function VideoPlayerProvider({ children }) {
  const [course, setCourse] = useState(null);
  const [currentVideoId, setCurrentVideoId] = useState(null);
  // The active quiz selection. When non-null, the course detail page renders
  // the quiz panel in place of the video player.
  const [currentQuiz, setCurrentQuiz] = useState(null); // { sectionId, quizId } | null
  // The active interactive activity selection. Mutually exclusive with quiz
  // and video.
  const [currentActivity, setCurrentActivity] = useState(null); // { sectionId, activityId } | null

  const playlist = useMemo(() => buildPlaylist(course), [course]);

  const currentIndex = useMemo(
    () => playlist.findIndex((v) => v.id === currentVideoId),
    [playlist, currentVideoId]
  );

  const currentVideo = currentIndex >= 0 ? playlist[currentIndex] : null;
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < playlist.length - 1;

  const loadCourse = useCallback((nextCourse, initialVideoId = null) => {
    setCourse(nextCourse);
    setCurrentQuiz(null);
    setCurrentActivity(null);
    const firstId =
      initialVideoId ??
      nextCourse?.sections?.flatMap((s) => s.videos || [])?.[0]?.id ??
      null;
    setCurrentVideoId(firstId);
  }, []);

  const selectVideo = useCallback(
    (videoId) => {
      if (playlist.some((v) => v.id === videoId)) {
        setCurrentVideoId(videoId);
        setCurrentQuiz(null);
        setCurrentActivity(null);
      }
    },
    [playlist]
  );

  const selectQuiz = useCallback((sectionId, quizId) => {
    setCurrentQuiz({ sectionId, quizId });
    setCurrentActivity(null);
  }, []);

  const selectActivity = useCallback((sectionId, activityId) => {
    setCurrentActivity({ sectionId, activityId });
    setCurrentQuiz(null);
  }, []);

  const playNext = useCallback(() => {
    if (hasNext) {
      setCurrentVideoId(playlist[currentIndex + 1].id);
      setCurrentQuiz(null);
      setCurrentActivity(null);
    }
  }, [hasNext, playlist, currentIndex]);

  const playPrevious = useCallback(() => {
    if (hasPrevious) {
      setCurrentVideoId(playlist[currentIndex - 1].id);
      setCurrentQuiz(null);
      setCurrentActivity(null);
    }
  }, [hasPrevious, playlist, currentIndex]);

  const reset = useCallback(() => {
    setCourse(null);
    setCurrentVideoId(null);
    setCurrentQuiz(null);
    setCurrentActivity(null);
  }, []);

  const value = useMemo(
    () => ({
      course,
      playlist,
      currentVideo,
      currentIndex,
      currentQuiz,
      currentActivity,
      hasPrevious,
      hasNext,
      loadCourse,
      selectVideo,
      selectQuiz,
      selectActivity,
      playNext,
      playPrevious,
      reset,
    }),
    [
      course,
      playlist,
      currentVideo,
      currentIndex,
      currentQuiz,
      currentActivity,
      hasPrevious,
      hasNext,
      loadCourse,
      selectVideo,
      selectQuiz,
      selectActivity,
      playNext,
      playPrevious,
      reset,
    ]
  );

  return (
    <VideoPlayerContext.Provider value={value}>
      {children}
    </VideoPlayerContext.Provider>
  );
}

export function useVideoPlayer() {
  const ctx = useContext(VideoPlayerContext);
  if (!ctx) {
    throw new Error("useVideoPlayer must be used inside <VideoPlayerProvider>");
  }
  return ctx;
}
