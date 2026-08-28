/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WIFIDECK_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
