export const SCENE_COUNT = 6;
export const FREE_SCENE_COUNT = 4;
export type StorySceneCount = 4 | 6;
export const FREE_SCENE_BEATS = ["setup", "inciting_incident", "climax", "resolution"] as const;
export const SCENE_BEATS = ["setup", "inciting_incident", "first_attempt", "setback", "climax", "resolution"] as const;
export type SceneBeat = (typeof SCENE_BEATS)[number];
export const BEAT_LABELS: Record<SceneBeat, string> = {
  setup: "Setup",
  inciting_incident: "Inciting Incident",
  first_attempt: "First Attempt",
  setback: "Setback",
  climax: "Climax",
  resolution: "Resolution",
};

export interface StorySceneMarker {
  index: number; // zero-based, matching image messages
  title: string;
  text: string;
}

/** Parse explicit scene indices instead of guessing from paragraphs or array length. */
export function parseSceneMarkers(story: string): StorySceneMarker[] {
  const markers: StorySceneMarker[] = [];
  const pattern = /\[SCENE\s+([1-6])(?::\s*([^\]\r\n]+))?\]/g;
  const matches = Array.from((story || "").matchAll(pattern));
  matches.forEach((match, position) => {
    const start = (match.index ?? 0) + match[0].length;
    const end = position + 1 < matches.length ? matches[position + 1].index : story.length;
    const index = Number(match[1]) - 1;
    if (markers.some(marker => marker.index === index)) return;
    markers.push({ index, title: match[2]?.trim() || `Scene ${index + 1}`, text: story.slice(start, end).trim() });
  });
  return markers;
}

/** Only request-scoped events belonging to the active generation may update its UI. */
export function isActiveStoryEvent(requestId: string | null | undefined, activeRequestId: string | null): boolean {
  return !!activeRequestId && requestId === activeRequestId;
}

export interface GeneratedImage {
  index: number;
  base64?: string;
  gcs_url?: string;
  format: string;
  stored_in_bucket?: boolean;
  error?: string;
  placeholder?: boolean;
}

/** Keep a fixed six-slot board; ignore invalid/duplicate indices and stale batches. */
export function placeImage(
  previous: (GeneratedImage | null)[],
  image: GeneratedImage,
  requestId?: string,
  activeRequestId?: string,
  sceneCount: StorySceneCount = SCENE_COUNT,
): (GeneratedImage | null)[] {
  const next = Array.from({ length: sceneCount }, (_, index) => previous[index] ?? null);
  if (requestId !== activeRequestId) return next;
  if (!Number.isInteger(image.index) || image.index < 0 || image.index >= sceneCount) return next;
  next[image.index] = image;
  return next;
}

export function emptyImageSlots(sceneCount: StorySceneCount = SCENE_COUNT): (GeneratedImage | null)[] {
  return Array.from({ length: sceneCount }, () => null);
}
