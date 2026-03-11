// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

// ─── Social Accounts ─────────────────────────────────────────────────────────

export enum Platform {
  youtube = "youtube",
  tiktok = "tiktok",
  instagram = "instagram",
  facebook = "facebook",
}

export interface SocialAccount {
  id: string;
  user_id: string;
  platform: Platform;
  account_name: string;
  account_avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

// ─── Job Status ───────────────────────────────────────────────────────────────

export enum JobStatus {
  PENDING_UPLOAD = "PENDING_UPLOAD",
  UPLOAD_IN_PROGRESS = "UPLOAD_IN_PROGRESS",
  UPLOAD_COMPLETE = "UPLOAD_COMPLETE",
  TRANSCRIPTION_IN_PROGRESS = "TRANSCRIPTION_IN_PROGRESS",
  TRANSCRIPTION_COMPLETE = "TRANSCRIPTION_COMPLETE",
  HOOK_GENERATION_IN_PROGRESS = "HOOK_GENERATION_IN_PROGRESS",
  HOOK_GENERATION_COMPLETE = "HOOK_GENERATION_COMPLETE",
  HOOK_APPROVED = "HOOK_APPROVED",
  WAITING_FOR_SOCIAL_CONNECTION = "WAITING_FOR_SOCIAL_CONNECTION",
  DESTINATIONS_SELECTED = "DESTINATIONS_SELECTED",
  PUBLISHING_IN_PROGRESS = "PUBLISHING_IN_PROGRESS",
  PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED",
  PUBLISHED = "PUBLISHED",
  SCHEDULED = "SCHEDULED",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
}

// ─── Content Job ──────────────────────────────────────────────────────────────

export interface ContentJob {
  id: string;
  user_id: string;
  title: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  approved_hook_id: string | null;
  scheduled_at_utc: string | null;
  user_timezone: string | null;
}

// ─── Job Asset ────────────────────────────────────────────────────────────────

export type AssetType = "original_video" | "processed_video" | "thumbnail" | "transcript";

export interface JobAsset {
  id: string;
  job_id: string;
  asset_type: AssetType;
  storage_key: string;
  file_size: number | null;
  duration_seconds: number | null;
  created_at: string;
}

// ─── Job Hook ─────────────────────────────────────────────────────────────────

export interface JobHook {
  id: string;
  job_id: string;
  text: string;
  rationale: string;
  score: number;
  is_selected: boolean;
  is_manually_edited: boolean;
  created_at: string;
}

// ─── Publish Target ───────────────────────────────────────────────────────────

export type PublishTargetStatus =
  | "pending"
  | "in_progress"
  | "published"
  | "failed"
  | "scheduled";

export interface PublishTarget {
  id: string;
  job_id: string;
  social_account_id: string;
  platform: Platform;
  status: PublishTargetStatus;
  published_at: string | null;
  external_post_url: string | null;
  error_message: string | null;
  created_at: string;
}

// ─── Wizard ───────────────────────────────────────────────────────────────────

export enum WizardStep {
  Upload = 1,
  Hooks = 2,
  Approve = 3,
  Platforms = 4,
  Publish = 5,
}

// ─── API ──────────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { msg: string; type: string }[];
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface PresignedUploadResponse {
  upload_url: string;
  storage_key: string;
  fields?: Record<string, string>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
