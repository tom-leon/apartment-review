/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the API, no trailing slash. Empty in tests, so paths stay relative. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
