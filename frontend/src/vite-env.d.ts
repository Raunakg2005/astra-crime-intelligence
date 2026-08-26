/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the analytics API. Empty in local dev (Vite proxies /api → :8000);
   *  set to the Catalyst AppSail URL at build time for production. */
  readonly VITE_API_BASE?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
