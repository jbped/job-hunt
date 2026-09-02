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
    __SESSION_TOKEN__?: string;
  }
}

export {};
