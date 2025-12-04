/// <reference types="vite/client" />

declare interface ImportMetaEnv {
  readonly VITE_AUTH_BASE_URL?: string
  readonly VITE_MODULE_AUTH_URL?: string
  readonly VITE_MODULE_LEDGER_URL?: string
  readonly VITE_MODULE_INVENTORY_URL?: string
  readonly VITE_MODULE_POS_URL?: string
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv
}
