import { useEffect, useRef, useState } from "react";
import { useTranslations } from "../i18n";
import { synthesizeSpeech } from "../client/apiClient";
import { SpeakerIcon } from "./icons";
import { Spinner } from "./Spinner";

/** Plays narration with real transport controls.
 *
 * Audio that can only be started is a trap: a reviewer who starts a
 * long narration by accident has no way to stop it, and screen-reader
 * users get two voices talking over each other. Play, pause, resume and
 * stop are all reachable, and progress is exposed so the control says
 * how much is left rather than only that something is happening.
 */
type PlaybackState = "idle" | "loading" | "playing" | "paused";

export function ListenButton({ text }: { text: string }) {
  const t = useTranslations();
  const [state, setState] = useState<PlaybackState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const audioUrlRef = useRef<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // The object URL is owned by this component, so it has to be released
  // when the component goes away or the narration text changes -
  // switching tickets otherwise leaks one blob per ticket viewed.
  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
      audioRef.current = null;
    };
  }, [text]);

  function attachHandlers(audio: HTMLAudioElement) {
    audio.addEventListener("timeupdate", () => {
      setProgress(audio.duration > 0 ? audio.currentTime / audio.duration : 0);
    });
    audio.addEventListener("ended", () => {
      setState("idle");
      setProgress(0);
    });
    audio.addEventListener("error", () => {
      setState("idle");
      setError(t.message.listenErrorPrefix);
    });
  }

  async function handlePlay() {
    setError(null);

    if (audioRef.current) {
      void audioRef.current.play();
      setState("playing");
      return;
    }

    setState("loading");
    const result = await synthesizeSpeech(text);

    if (!result.ok) {
      setState("idle");
      setError(result.error);
      return;
    }

    audioUrlRef.current = result.data.url;
    const audio = new Audio(result.data.url);
    audioRef.current = audio;
    attachHandlers(audio);
    void audio.play();
    setState("playing");
  }

  function handlePause() {
    audioRef.current?.pause();
    setState("paused");
  }

  function handleStop() {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setProgress(0);
    setState("idle");
  }

  const loading = state === "loading";
  const started = state === "playing" || state === "paused";
  const playLabel = progress > 0 ? t.message.replayButton : t.message.listenButton;

  return (
    <span className="listen-control">
      {state !== "playing" && (
        <button type="button" onClick={handlePlay} disabled={loading} aria-busy={loading}>
          {loading ? <Spinner /> : <SpeakerIcon width={14} height={14} />}
          {loading ? t.message.listenLoading : state === "paused" ? t.message.resumeButton : playLabel}
        </button>
      )}

      {state === "playing" && (
        <button type="button" onClick={handlePause}>
          {t.message.pauseButton}
        </button>
      )}

      {started && (
        <button type="button" onClick={handleStop}>
          {t.message.stopButton}
        </button>
      )}

      {started && (
        <progress
          className="listen-progress"
          max={1}
          value={progress}
          aria-label={t.message.progressLabel}
        />
      )}

      {error && (
        <span className="guide-text" role="alert">
          {t.message.listenErrorPrefix} {error}
        </span>
      )}
    </span>
  );
}
