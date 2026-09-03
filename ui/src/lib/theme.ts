export const BASE_COLORS = [
  "mist",
  "neutral",
  "stone",
  "zinc",
  "taupe",
  "mauve",
  "olive",
] as const;
export const COLOR_MODES = ["system", "light", "dark"] as const;

export type BaseColor = (typeof BASE_COLORS)[number];
export type ColorMode = (typeof COLOR_MODES)[number];
export type Appearance = { mode: ColorMode; baseColor: BaseColor };

export const DEFAULT_APPEARANCE: Appearance = {
  mode: "system",
  baseColor: "mist",
};

const STORAGE_KEY = "ce.appearance";
const DARK_QUERY = "(prefers-color-scheme: dark)";

function readAppearance(): Appearance {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_APPEARANCE;
    const parsed = JSON.parse(raw) as Partial<Appearance>;
    return {
      mode: COLOR_MODES.includes(parsed.mode as ColorMode)
        ? (parsed.mode as ColorMode)
        : DEFAULT_APPEARANCE.mode,
      baseColor: BASE_COLORS.includes(parsed.baseColor as BaseColor)
        ? (parsed.baseColor as BaseColor)
        : DEFAULT_APPEARANCE.baseColor,
    };
  } catch {
    return DEFAULT_APPEARANCE;
  }
}

export function applyAppearance(appearance: Appearance): void {
  const root = document.documentElement;
  const dark =
    appearance.mode === "dark" ||
    (appearance.mode === "system" && window.matchMedia(DARK_QUERY).matches);
  root.classList.toggle("dark", dark);
  root.dataset.baseColor = appearance.baseColor;
  root.style.colorScheme = dark ? "dark" : "light";
}

let current = readAppearance();
const listeners = new Set<() => void>();

export function getAppearance(): Appearance {
  return current;
}

export function setAppearance(patch: Partial<Appearance>): void {
  current = { ...current, ...patch };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch {
    /* a browser refusing storage still gets the change for this session */
  }
  applyAppearance(current);
  for (const listener of listeners) listener();
}

export function subscribeAppearance(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Called once at startup; the media listener keeps "system" honest. */
export function startAppearance(): void {
  applyAppearance(current);
  window.matchMedia(DARK_QUERY).addEventListener("change", () => {
    if (current.mode === "system") applyAppearance(current);
  });
}
