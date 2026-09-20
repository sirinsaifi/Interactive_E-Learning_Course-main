export function formatDuration(totalSeconds) {
  const safeTotal = Math.max(0, Number(totalSeconds) || 0);
  const hours = Math.floor(safeTotal / 3600);
  const minutes = Math.floor((safeTotal % 3600) / 60);
  const seconds = Math.floor(safeTotal % 60);
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function formatTotalDuration(totalSeconds) {
  const safeTotal = Math.max(0, Number(totalSeconds) || 0);
  const hours = Math.floor(safeTotal / 3600);
  const minutes = Math.floor((safeTotal % 3600) / 60);
  if (hours === 0 && minutes === 0) return "—";
  if (hours === 0) return `${minutes}m`;
  return `${hours}h ${minutes}m`;
}
