"use client";

import { useState } from 'react';
import { Download, Expand, ImageOff, Loader2 } from 'lucide-react';
import { BEAT_LABELS, FREE_SCENE_BEATS, GeneratedImage, SCENE_BEATS, SCENE_COUNT, StorySceneCount, parseSceneMarkers } from '@/lib/story-contract';

interface StoryFramesProps {
  story: string;
  images?: (GeneratedImage | null)[];
  isGeneratingStory?: boolean;
  isGeneratingImages?: boolean;
  generationStatus?: string;
  sceneCount?: StorySceneCount;
}

function imageSource(image: GeneratedImage, failedUrl?: string): string {
  if (image.gcs_url && image.gcs_url !== failedUrl) return image.gcs_url;
  return image.base64 ? `data:image/${image.format || 'png'};base64,${image.base64}` : '';
}

function SceneImage({ image, index, generating }: { image: GeneratedImage | null; index: number; generating: boolean }) {
  const [failedUrl, setFailedUrl] = useState<string>();
  const src = image && !image.placeholder && !image.error ? imageSource(image, failedUrl) : '';
  if (!src) {
    return (
      <div className="aspect-video flex flex-col items-center justify-center gap-2 bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300" role="status">
        {image?.error || image?.placeholder ? <ImageOff className="h-6 w-6" aria-hidden="true" /> : generating ? <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" /> : <ImageOff className="h-6 w-6 opacity-40" aria-hidden="true" />}
        <span className="text-sm">{image?.error || image?.placeholder ? 'Illustration unavailable' : generating ? 'Waiting for illustration…' : `Illustration ${index + 1}`}</span>
      </div>
    );
  }
  const openImage = async () => {
    try {
      // Blob URLs avoid injecting server-provided strings into a new document.
      const response = await fetch(src);
      if (!response.ok) throw new Error('Image could not be loaded');
      const url = URL.createObjectURL(await response.blob());
      window.open(url, '_blank', 'noopener,noreferrer');
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      setFailedUrl(src);
    }
  };
  return (
    <div className="relative aspect-video bg-stone-100 dark:bg-stone-800">
      {/* Signed GCS URLs and inline fallbacks do not need Next's image optimizer. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={`Illustration for scene ${index + 1}`} className="h-full w-full object-cover" onError={() => setFailedUrl(src)} />
      <div className="absolute bottom-2 right-2 flex gap-2">
        <button type="button" onClick={openImage} aria-label={`View scene ${index + 1} illustration full size`} className="rounded-lg bg-white/90 p-2 text-stone-800 shadow hover:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"><Expand className="h-4 w-4" /></button>
        <a href={src} download={`story-scene-${index + 1}.png`} aria-label={`Download scene ${index + 1} illustration`} className="rounded-lg bg-white/90 p-2 text-stone-800 shadow hover:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600"><Download className="h-4 w-4" /></a>
      </div>
    </div>
  );
}

export default function StoryFrames({ story, images = [], isGeneratingStory = false, isGeneratingImages = false, generationStatus = '', sceneCount = SCENE_COUNT }: StoryFramesProps) {
  const markers = parseSceneMarkers(story);
  const beats = sceneCount === 4 ? FREE_SCENE_BEATS : SCENE_BEATS;
  const scenes = Array.from({ length: sceneCount }, (_, index) => markers.find(marker => marker.index === index));
  const completed = images.slice(0, sceneCount).filter(image => image && !image.error && !image.placeholder && (image.gcs_url || image.base64)).length;
  return (
    <section className="w-full space-y-6" aria-labelledby="story-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700 dark:text-teal-300">Your little adventure</p>
          <h2 id="story-heading" className="mt-1 text-2xl font-bold text-stone-900 dark:text-stone-50">{sceneCount === 4 ? "Four" : "Six"} scenes, one story</h2>
        </div>
        <p className="text-sm text-stone-600 dark:text-stone-300" aria-live="polite">{generationStatus || `${completed} of ${sceneCount} illustrations ready`}</p>
      </div>
      {story && markers.length === 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900" role="status">
          <p className="font-medium">This story has no scene boundaries. Showing the original text without guessing.</p>
          <p className="mt-2 whitespace-pre-wrap">{story}</p>
        </div>
      )}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {scenes.map((scene, index) => (
          <article key={index} className="overflow-hidden rounded-2xl border border-orange-200/80 bg-white shadow-sm dark:border-orange-900/50 dark:bg-stone-900" aria-label={`Scene ${index + 1}: ${scene?.title || BEAT_LABELS[beats[index]]}`}>
            <SceneImage image={images[index] ?? null} index={index} generating={isGeneratingImages} />
            <div className="p-5 md:p-6">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-300">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-50 dark:bg-teal-950">{index + 1}</span>
                {BEAT_LABELS[beats[index]]}
              </div>
              <h3 className="mb-2 text-lg font-semibold text-stone-900 dark:text-stone-50">{scene?.title || BEAT_LABELS[beats[index]]}</h3>
              {scene?.text ? <p className="leading-7 text-stone-700 dark:text-stone-200">{scene.text}</p> : (
                <div className="flex min-h-24 items-center gap-2 text-sm text-stone-500 dark:text-stone-400">
                  {isGeneratingStory ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Writing this scene…</> : 'This scene will appear here.'}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
