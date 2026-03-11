import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";
import { JobStatus, Platform } from "@/types";

// ─── Classnames ───────────────────────────────────────────────────────────────

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// ─── Date helpers ─────────────────────────────────────────────────────────────

export function formatDate(
  dateStr: string | null | undefined,
  fmt = "MMM d, yyyy",
): string {
  if (!dateStr) return "—";
  try {
    return format(new Date(dateStr), fmt);
  } catch {
    return "—";
  }
}

export function formatDateRelative(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return "—";
  }
}

// ─── File size ────────────────────────────────────────────────────────────────

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ─── Job status helpers ───────────────────────────────────────────────────────

const STATUS_LABELS: Record<JobStatus, string> = {
  [JobStatus.PENDING_UPLOAD]: "Pending Upload",
  [JobStatus.UPLOAD_IN_PROGRESS]: "Uploading…",
  [JobStatus.UPLOAD_COMPLETE]: "Upload Complete",
  [JobStatus.TRANSCRIPTION_IN_PROGRESS]: "Transcribing…",
  [JobStatus.TRANSCRIPTION_COMPLETE]: "Transcription Done",
  [JobStatus.HOOK_GENERATION_IN_PROGRESS]: "Generating Hooks…",
  [JobStatus.HOOK_GENERATION_COMPLETE]: "Hooks Ready",
  [JobStatus.HOOK_APPROVED]: "Hook Approved",
  [JobStatus.WAITING_FOR_SOCIAL_CONNECTION]: "Connect Socials",
  [JobStatus.DESTINATIONS_SELECTED]: "Destinations Set",
  [JobStatus.PUBLISHING_IN_PROGRESS]: "Publishing…",
  [JobStatus.PARTIALLY_PUBLISHED]: "Partially Published",
  [JobStatus.PUBLISHED]: "Published",
  [JobStatus.SCHEDULED]: "Scheduled",
  [JobStatus.FAILED]: "Failed",
  [JobStatus.CANCELLED]: "Cancelled",
};

export function getStatusLabel(status: JobStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function getStatusColor(
  status: JobStatus,
): string {
  switch (status) {
    case JobStatus.PUBLISHED:
      return "green";
    case JobStatus.SCHEDULED:
      return "blue";
    case JobStatus.FAILED:
    case JobStatus.CANCELLED:
      return "red";
    case JobStatus.PUBLISHING_IN_PROGRESS:
    case JobStatus.TRANSCRIPTION_IN_PROGRESS:
    case JobStatus.HOOK_GENERATION_IN_PROGRESS:
    case JobStatus.UPLOAD_IN_PROGRESS:
      return "yellow";
    case JobStatus.PARTIALLY_PUBLISHED:
      return "orange";
    default:
      return "gray";
  }
}

// ─── Platform helpers ─────────────────────────────────────────────────────────

export function getPlatformLabel(platform: Platform): string {
  const labels: Record<Platform, string> = {
    [Platform.youtube]: "YouTube",
    [Platform.tiktok]: "TikTok",
    [Platform.instagram]: "Instagram",
    [Platform.facebook]: "Facebook",
  };
  return labels[platform] ?? platform;
}

export function getPlatformColor(platform: Platform): string {
  const colors: Record<Platform, string> = {
    [Platform.youtube]: "bg-red-100 text-red-700",
    [Platform.tiktok]: "bg-gray-900 text-white",
    [Platform.instagram]: "bg-pink-100 text-pink-700",
    [Platform.facebook]: "bg-blue-100 text-blue-700",
  };
  return colors[platform] ?? "bg-gray-100 text-gray-700";
}

// Kept for backwards compatibility – callers that just want a string icon name
export function getPlatformIcon(platform: Platform): string {
  return platform;
}

// ─── Error message helper ─────────────────────────────────────────────────────

export function getErrorMessage(error: unknown): string {
  if (!error) return "An unknown error occurred.";
  if (typeof error === "string") return error;
  if (
    typeof error === "object" &&
    "response" in error &&
    (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
  ) {
    const detail = (error as { response: { data: { detail: unknown } } })
      .response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg ?? "Error").join("; ");
    }
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}
