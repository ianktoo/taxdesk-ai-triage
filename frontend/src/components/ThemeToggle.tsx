import { useTheme } from "../theme/useTheme";
import { SunIcon, MoonIcon } from "./icons";

export function ThemeToggle() {
  const [theme, toggle] = useTheme();

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? <SunIcon width={16} height={16} /> : <MoonIcon width={16} height={16} />}
    </button>
  );
}
