/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Dev-only: the vault's write token, since only the served page gets the
   *  placeholder substituted. */
  readonly VITE_SESSION_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare global {
  interface Window {
    /** Deliberately not named `__SESSION_TOKEN__`: serve.py replaces every
     *  occurrence of that literal in index.html, so a property of that name
     *  would be renamed along with its value. */
    __CE_SESSION_TOKEN__?: string;
  }
}

export {};
