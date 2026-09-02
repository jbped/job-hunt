/// <reference types="vite/client" />

declare global {
  interface Window {
    __SESSION_TOKEN__?: string;
  }
}

export {};
