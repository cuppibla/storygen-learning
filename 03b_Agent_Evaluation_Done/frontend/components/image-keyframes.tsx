"use client";

import { Loader2 } from 'lucide-react';
import { BEAT_LABELS, GeneratedImage, SCENE_BEATS, SCENE_COUNT } from '@/lib/story-contract';

interface ImageKeyframesProps {
  images?: (GeneratedImage | null)[];
  isGenerating?: boolean;
  generationStatus?: string;
}

export default function ImageKeyframes({ images = [], isGenerating = false, generationStatus = '' }: ImageKeyframesProps) {
  const completed = images.filter(image => image && !image.error && !image.placeholder && (image.gcs_url || image.base64)).length;
  return (
    <section className="space-y-4" aria-label="Story keyframes">
      <h3 className="text-xl font-semibold text-stone-800 dark:text-stone-100">Story keyframes</h3>
      <p className="text-sm text-stone-600 dark:text-stone-300" aria-live="polite">{generationStatus || `${completed} of ${SCENE_COUNT} illustrations ready`}</p>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        {Array.from({ length: SCENE_COUNT }, (_, index) => {
          const image = images[index];
          const src = image && !image.error && !image.placeholder ? image.gcs_url || (image.base64 ? `data:image/${image.format};base64,${image.base64}` : '') : '';
          return (
            <figure key={index} className="overflow-hidden rounded-xl bg-stone-100 dark:bg-stone-800">
              <div className="aspect-video flex items-center justify-center">
                {src ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={src} alt={`Scene ${index + 1} keyframe`} className="h-full w-full object-cover" /> : isGenerating ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Generating illustration" /> : <span className="text-sm text-stone-500">{image?.error ? 'Unavailable' : `Scene ${index + 1}`}</span>}
              </div>
              <figcaption className="p-2 text-xs text-stone-600 dark:text-stone-300">{index + 1} · {BEAT_LABELS[SCENE_BEATS[index]]}</figcaption>
            </figure>
          );
        })}
      </div>
    </section>
  );
}
