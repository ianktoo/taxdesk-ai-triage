import { useRef, useState } from "react";
import { useTranslations } from "../i18n";
import { synthesizeSpeech } from "../client/apiClient";
import { SpeakerIcon } from "./icons";
import { Spinner } from "./Spinner";

export function ListenButton({ text }: { text: string }) {
  const t = useTranslations();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function handleClick() {
    setError(null);

    if (audioUrlRef.current && audioRef.current) {
      audioRef.current.currentTime = 0;
      void audioRef.current.play();
      return;
    }

    setLoading(true);
    const result = await synthesizeSpeech(text);
    setLoading(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }

    audioUrlRef.current = result.data.url;
    const audio = new Audio(result.data.url);
    audioRef.current = audio;
    void audio.play();
  }

  return (
    <span className="listen-control">
      <button type="button" onClick={handleClick} disabled={loading} aria-busy={loading}>
        {loading ? <Spinner /> : <SpeakerIcon width={14} height={14} />}
        {loading ? t.message.listenLoading : t.message.listenButton}
      </button>
      {error && (
        <span className="guide-text" role="alert" style={{ margin: 0 }}>
          {t.message.listenErrorPrefix} {error}
        </span>
      )}
    </span>
  );
}
