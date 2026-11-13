"use client";

import { useState } from 'react';
import { BookOpen, Loader2, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import StoryFrames from '@/components/story-frames';
import { useStorySocket } from '@/lib/use-story-socket';

type Choice = 'free' | 'upgrade' | null;

export default function Home() {
  const { theme, setTheme } = useTheme();
  const [choice, setChoice] = useState<Choice>(null);
  const [adventure, setAdventure] = useState('animals');
  const [companion, setCompanion] = useState('none');
  const [showStory, setShowStory] = useState(false);
  const { isConnected, isConnecting, isGenerating, isGeneratingImages, story, images, status, error, connect, generateFree } = useStorySocket();

  const handleGenerate = () => {
    if (generateFree({ adventure, companion })) setShowStory(true);
  };

  return (
    <main className="min-h-screen bg-orange-50/40 px-4 py-8 dark:bg-stone-950 md:py-14">
      <div className="mx-auto max-w-5xl">
        <header className="mb-10 flex items-center justify-between gap-3">
          <a href="/" className="flex items-center gap-2 text-xl font-bold text-stone-900 dark:text-stone-50"><BookOpen className="h-6 w-6 text-teal-700" /> StoryGen</a>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-white px-3 py-1.5 text-xs text-stone-600 shadow-sm dark:bg-stone-800 dark:text-stone-300" role="status">{isConnected ? 'Connected' : isConnecting ? 'Connecting…' : 'Disconnected'}</span>
            <button type="button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} className="rounded-full bg-white p-2 text-stone-700 shadow-sm dark:bg-stone-800 dark:text-stone-200" aria-label="Toggle color theme">{theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}</button>
          </div>
        </header>
        <section className="mx-auto mb-12 max-w-3xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-teal-700 dark:text-teal-300">Small ideas. Meaningful adventures.</p>
          <h1 className="text-4xl font-bold tracking-tight text-stone-900 dark:text-stone-50 md:text-5xl">A little story, made for storytime.</h1>
          <p className="mt-4 text-lg text-stone-600 dark:text-stone-300">Choose a complete free story, or discover the planned personalised upgrade.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2" aria-label="Choose a story option">
            <button type="button" disabled={isGenerating} onClick={() => setChoice('free')} aria-pressed={choice === 'free'} className="rounded-2xl border-2 border-teal-700 bg-white p-6 text-left text-stone-900 shadow-sm hover:bg-teal-50 disabled:opacity-60 dark:bg-stone-900 dark:text-stone-50"><span className="block text-xl font-bold">Free</span><span className="mt-2 block text-sm">A complete four-scene adventure with a fictional hero.</span></button>
            <button type="button" disabled={isGenerating} onClick={() => setChoice('upgrade')} aria-pressed={choice === 'upgrade'} className="rounded-2xl border-2 border-stone-300 bg-white p-6 text-left text-stone-900 shadow-sm hover:bg-orange-50 disabled:opacity-60 dark:border-stone-700 dark:bg-stone-900 dark:text-stone-50"><span className="block text-xl font-bold">Upgrade</span><span className="mt-2 block text-sm">A personalised six-scene story, planned for a one-time purchase.</span></button>
          </div>
          {error && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-left text-sm text-red-800"><p>{error}</p><button type="button" onClick={connect} className="mt-2 font-semibold underline">Try reconnecting</button></div>}
          {choice === 'free' && <form className="mt-8 rounded-2xl bg-white p-6 text-left shadow-sm dark:bg-stone-900" onSubmit={event => { event.preventDefault(); if (!isGenerating) handleGenerate(); }}>
            <h2 className="text-xl font-bold text-stone-900 dark:text-stone-50">Your free story</h2>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-300">Choose an adventure and an optional fictional companion. No child’s name is needed.</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-semibold text-stone-700 dark:text-stone-200">Adventure<select value={adventure} onChange={e => setAdventure(e.target.value)} disabled={isGenerating} className="mt-2 block w-full rounded-xl border border-stone-300 bg-white p-3 text-stone-900"><option value="animals">Animals</option><option value="ocean">Ocean</option><option value="space">Space</option><option value="magic">Magic</option><option value="mystery">Mystery</option></select></label>
              <label className="text-sm font-semibold text-stone-700 dark:text-stone-200">Companion<select value={companion} onChange={e => setCompanion(e.target.value)} disabled={isGenerating} className="mt-2 block w-full rounded-xl border border-stone-300 bg-white p-3 text-stone-900"><option value="none">No preference</option><option value="animal">Animal</option><option value="robot">Robot</option><option value="dragon">Dragon</option><option value="teddy">Teddy</option></select></label>
            </div>
            <button type="submit" disabled={isGenerating || !isConnected} className="mt-5 flex items-center justify-center gap-2 rounded-xl bg-teal-700 px-6 py-3 font-semibold text-white hover:bg-teal-800 disabled:opacity-50">{isGenerating && <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />}{isGenerating ? 'Creating your story…' : 'Create free story'}</button>
            <p className="mt-3 text-xs text-stone-500">Four illustrations are generated; provider usage charges apply to the operator.</p>
          </form>}
          {choice === 'upgrade' && <div className="mt-8 rounded-2xl border border-orange-200 bg-white p-6 text-left dark:border-stone-700 dark:bg-stone-900"><h2 className="text-xl font-bold text-stone-900 dark:text-stone-50">Personalised story — coming soon</h2><p className="mt-2 text-sm text-stone-600 dark:text-stone-300">The one-time personalised upgrade and secure checkout are still being built. No payment can be taken yet. You can choose Free now.</p></div>}
          {status && <p className="mt-4 text-sm text-teal-700 dark:text-teal-300" aria-live="polite">{status}</p>}
        </section>
        {showStory && <StoryFrames sceneCount={4} story={story} images={images} isGeneratingStory={isGenerating && !story} isGeneratingImages={isGeneratingImages} generationStatus={status} />}
        <footer className="mt-12 text-center text-xs text-stone-500 dark:text-stone-400">AI-generated stories and illustrations are best enjoyed together with a grown-up.</footer>
      </div>
    </main>
  );
}
