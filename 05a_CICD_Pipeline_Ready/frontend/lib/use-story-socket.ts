"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import { emptyImageSlots, GeneratedImage, isActiveStoryEvent, placeImage } from '@/lib/story-contract';

interface ServerMessage {
  type: string;
  data?: string | GeneratedImage;
  message?: string;
  turn_complete?: boolean;
  request_id?: string | null;
}

export function useStorySocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGeneratingImages, setIsGeneratingImages] = useState(false);
  const [story, setStory] = useState('');
  const [images, setImages] = useState<(GeneratedImage | null)[]>(emptyImageSlots);
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptsRef = useRef(0);
  const mountedRef = useRef(false);
  const connectRef = useRef<() => void>(() => {});
  const userId = useRef(`user-${Math.random().toString(36).slice(2)}`);
  const activeRequestRef = useRef<string | null>(null);
  const sceneCountRef = useRef<4 | 6>(6);

  const connect = useCallback(() => {
    if (!mountedRef.current || socketRef.current?.readyState === WebSocket.OPEN || socketRef.current?.readyState === WebSocket.CONNECTING) return;
    if (retryRef.current) clearTimeout(retryRef.current);
    retryRef.current = null;
    setIsConnecting(true);
    setError(null);
    const base = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
    const url = base.replace(/^http/, 'ws') + `/ws/${userId.current}`;
    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      setIsConnecting(false);
      setError('The backend URL is invalid. Check NEXT_PUBLIC_BACKEND_URL in frontend/.env.local.');
      return;
    }
    socketRef.current = socket;
    socket.onopen = () => {
      if (socketRef.current !== socket) return;
      attemptsRef.current = 0;
      setIsConnected(true);
      setIsConnecting(false);
      setError(null);
    };
    socket.onmessage = event => {
      if (socketRef.current !== socket) return;
      let message: ServerMessage;
      try { message = JSON.parse(event.data); } catch { return; }
      if (!isActiveStoryEvent(message.request_id, activeRequestRef.current)) return;
      switch (message.type) {
        case 'processing':
          setIsGenerating(true);
          setStatus(message.message || `Writing your ${sceneCountRef.current}-scene story…`);
          break;
        case 'story_complete':
          if (typeof message.data === 'string') setStory(message.data);
          setIsGeneratingImages(true);
          setStatus(`Story ready. Illustrating ${sceneCountRef.current} scenes…`);
          break;
        case 'image_generated': {
          const image = message.data;
          if (typeof image === 'string' || !image || !Number.isInteger(image.index)) break;
          setImages(previous => placeImage(previous, image, undefined, undefined, sceneCountRef.current));
          setStatus(image.error ? `Scene ${image.index + 1}: illustration unavailable` : `Illustration ${image.index + 1} of ${sceneCountRef.current} ready`);
          break;
        }
        case 'turn_complete':
          setIsGenerating(false);
          setIsGeneratingImages(false);
          setStatus(`Your ${sceneCountRef.current}-scene story is ready.`);
          break;
        case 'error':
          setError(message.message || 'Story generation failed. Please try again.');
          setIsGenerating(false);
          setIsGeneratingImages(false);
          setStatus('');
          break;
      }
    };
    socket.onclose = event => {
      if (socketRef.current !== socket) return;
      socketRef.current = null;
      setIsConnected(false);
      setIsConnecting(false);
      setIsGenerating(false);
      setIsGeneratingImages(false);
      setStatus('');
      if (mountedRef.current && event.code !== 1000) {
        setError('Connection lost. Reconnecting; please retry the story after Connected appears.');
        const delay = Math.min(30_000, 1000 * 2 ** attemptsRef.current++);
        retryRef.current = setTimeout(() => connectRef.current(), delay);
      }
    };
    socket.onerror = () => {
      if (socketRef.current !== socket) return;
      setError('Cannot reach the story service. Check that the backend is running and its URL is correct.');
      setIsConnecting(false);
    };
  }, []);

  useEffect(() => {
    connectRef.current = connect;
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (retryRef.current) clearTimeout(retryRef.current);
      const socket = socketRef.current;
      socketRef.current = null;
      socket?.close(1000, 'Page closed');
    };
  }, [connect]);

  const generateRequest = useCallback((data: string | { adventure: string; companion: string }, free: boolean) => {
    const input = typeof data === "string" ? data.trim() : data;
    if (!free && (typeof input !== "string" || !input || input.length > 500)) {
      setError('Enter between 1 and 500 characters of story keywords.');
      return false;
    }
    if (socketRef.current?.readyState !== WebSocket.OPEN) {
      setError('Not connected yet. Please wait for Connected, then try again.');
      return false;
    }
    const requestId = globalThis.crypto?.randomUUID?.() || `request-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    activeRequestRef.current = requestId;
    sceneCountRef.current = free ? 4 : 6;
    setStory('');
    setImages(emptyImageSlots(sceneCountRef.current));
    setError(null);
    setIsGenerating(true);
    setIsGeneratingImages(false);
    setStatus(`Writing your ${sceneCountRef.current}-scene story…`);
    socketRef.current.send(JSON.stringify({ type: free ? 'generate_free_story' : 'generate_story', data: input, request_id: requestId }));
    return true;
  }, []);

  const generate = useCallback((keywords: string) => generateRequest(keywords, false), [generateRequest]);
  const generateFree = useCallback((options: { adventure: string; companion: string }) => generateRequest(options, true), [generateRequest]);

  return { isConnected, isConnecting, isGenerating, isGeneratingImages, story, images, status, error, connect, generate, generateFree };
}
