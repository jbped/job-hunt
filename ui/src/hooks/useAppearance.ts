import { useSyncExternalStore } from "react";
import {
  getAppearance,
  setAppearance,
  subscribeAppearance,
  type Appearance,
} from "../lib/theme";

export function useAppearance(): [
  Appearance,
  (patch: Partial<Appearance>) => void,
] {
  const appearance = useSyncExternalStore(
    subscribeAppearance,
    getAppearance,
    getAppearance,
  );
  return [appearance, setAppearance];
}
