import { useAppearance } from "../hooks/useAppearance";
import {
  BASE_COLORS,
  COLOR_MODES,
  type BaseColor,
  type ColorMode,
} from "../lib/theme";

/** Temporary home for the appearance settings: they belong on the Settings
 *  page the redesign introduces, and move there with it. */
export default function AppearanceControl() {
  const [appearance, update] = useAppearance();

  return (
    <span className="appearance">
      <label>
        <span className="sr-only">Theme</span>
        <select
          value={appearance.mode}
          aria-label="Theme"
          onChange={(e) => update({ mode: e.target.value as ColorMode })}
        >
          {COLOR_MODES.map((mode) => (
            <option key={mode} value={mode}>
              {mode}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span className="sr-only">Base color</span>
        <select
          value={appearance.baseColor}
          aria-label="Base color"
          onChange={(e) => update({ baseColor: e.target.value as BaseColor })}
        >
          {BASE_COLORS.map((color) => (
            <option key={color} value={color}>
              {color}
            </option>
          ))}
        </select>
      </label>
    </span>
  );
}
