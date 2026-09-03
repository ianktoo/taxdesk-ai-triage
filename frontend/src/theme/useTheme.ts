import { useCallback, useEffect, useState } from "react";

export type ThemeChoice = "light" | "dark";

const STORAGE_KEY = "taxdesk-theme";

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function readStoredTheme(): ThemeChoice | null {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
}

function applyTheme(theme: ThemeChoice) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function useTheme(): [ThemeChoice, () => void] {
  const [theme, setTheme] = useState<ThemeChoice>(() => {
    const stored = readStoredTheme();
    return stored ?? (systemPrefersDark() ? "dark" : "light");
  });

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: ThemeChoice = prev === "dark" ? "light" : "dark";
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // Storage unavailable (private browsing, etc.), the toggle still
        // works for this page load via React state alone.
      }
      return next;
    });
  }, []);

  return [theme, toggle];
}
