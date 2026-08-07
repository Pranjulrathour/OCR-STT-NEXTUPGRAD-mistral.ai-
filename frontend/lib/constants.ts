export const APP_NAME = "Mistral AI Workspace";

export const APP_DESCRIPTION =
  "Transform documents and speech into text — powered by Mistral AI. Fast, beautiful, production ready.";

export const GITHUB_URL = "https://github.com";

export const APP_VERSION = "1.0.0";

export const NAV_LINKS = [
  { href: "/ocr", label: "OCR" },
  { href: "/speech", label: "Speech" },
] as const;

export const MAX_OCR_FILE_SIZE_BYTES = 100 * 1024 * 1024;

export const ACCEPTED_OCR_FILE_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
] as const;
