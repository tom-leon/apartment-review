/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the API, no trailing slash. Empty in tests, so paths stay relative. */
  readonly VITE_API_URL?: string;
  /** Client ID of the Google OAuth web client the "Sign in with Google" button uses. */
  readonly VITE_GOOGLE_CLIENT_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

/** The part of Google's sign-in script (https://accounts.google.com/gsi/client) this app uses. */
interface GoogleIdConfig {
  client_id: string;
  callback: (response: { credential: string }) => void;
}

declare const google: {
  accounts: {
    id: {
      initialize(config: GoogleIdConfig): void;
      renderButton(parent: HTMLElement, options: { theme?: string; size?: string }): void;
    };
  };
};
