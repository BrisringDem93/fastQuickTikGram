import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  ContentJob,
  JobAsset,
  JobHook,
  PresignedUploadResponse,
  PublishTarget,
  SocialAccount,
  User,
} from "@/types";

// ─── Query keys ───────────────────────────────────────────────────────────────

export const queryKeys = {
  currentUser: ["currentUser"] as const,
  socialAccounts: ["socialAccounts"] as const,
  jobs: ["jobs"] as const,
  job: (id: string) => ["job", id] as const,
  jobAssets: (id: string) => ["jobAssets", id] as const,
  jobHooks: (id: string) => ["jobHooks", id] as const,
  publishTargets: (id: string) => ["publishTargets", id] as const,
};

// ─── Queries ─────────────────────────────────────────────────────────────────

export function useCurrentUser(): UseQueryResult<User> {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: () => api.get<User>("/auth/me").then((r) => r.data),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useSocialAccounts(): UseQueryResult<SocialAccount[]> {
  return useQuery({
    queryKey: queryKeys.socialAccounts,
    queryFn: () =>
      api.get<SocialAccount[]>("/social-accounts").then((r) => r.data),
    staleTime: 60_000,
  });
}

export function useJobs(): UseQueryResult<ContentJob[]> {
  return useQuery({
    queryKey: queryKeys.jobs,
    queryFn: () => api.get<ContentJob[]>("/jobs").then((r) => r.data),
    staleTime: 30_000,
  });
}

export function useJob(jobId: string): UseQueryResult<ContentJob> {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => api.get<ContentJob>(`/jobs/${jobId}`).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      const pollStatuses = [
        "UPLOAD_IN_PROGRESS",
        "TRANSCRIPTION_IN_PROGRESS",
        "HOOK_GENERATION_IN_PROGRESS",
        "PUBLISHING_IN_PROGRESS",
      ];
      return status && pollStatuses.includes(status) ? 3_000 : false;
    },
  });
}

export function useJobAssets(jobId: string): UseQueryResult<JobAsset[]> {
  return useQuery({
    queryKey: queryKeys.jobAssets(jobId),
    queryFn: () =>
      api.get<JobAsset[]>(`/jobs/${jobId}/assets`).then((r) => r.data),
    enabled: !!jobId,
  });
}

export function useJobHooks(jobId: string): UseQueryResult<JobHook[]> {
  return useQuery({
    queryKey: queryKeys.jobHooks(jobId),
    queryFn: () =>
      api.get<JobHook[]>(`/jobs/${jobId}/hooks`).then((r) => r.data),
    enabled: !!jobId,
  });
}

export function usePublishTargets(jobId: string): UseQueryResult<PublishTarget[]> {
  return useQuery({
    queryKey: queryKeys.publishTargets(jobId),
    queryFn: () =>
      api
        .get<PublishTarget[]>(`/jobs/${jobId}/publish-targets`)
        .then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const targets = query.state.data;
      if (!targets) return false;
      const hasInProgress = targets.some((t) => t.status === "in_progress");
      return hasInProgress ? 3_000 : false;
    },
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

export function useCreateJob(): UseMutationResult<
  ContentJob,
  Error,
  { title: string }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload) =>
      api.post<ContentJob>("/jobs", payload).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.jobs }),
  });
}

interface UploadVideoPayload {
  jobId: string;
  file: File;
  onProgress?: (pct: number) => void;
}

export function useUploadVideo(): UseMutationResult<
  JobAsset,
  Error,
  UploadVideoPayload
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, file, onProgress }) => {
      // 1. Get presigned URL
      const { data: presigned } = await api.post<PresignedUploadResponse>(
        `/jobs/${jobId}/upload-video`,
        {
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        },
      );

      // 2. Upload directly to S3
      await fetch(presigned.upload_url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });

      // 3. Confirm upload
      const { data: asset } = await api.post<JobAsset>(
        `/jobs/${jobId}/confirm-upload`,
        {
          storage_key: presigned.storage_key,
          file_size: file.size,
        },
        {
          onUploadProgress: (e) => {
            if (onProgress && e.total) {
              onProgress(Math.round((e.loaded / e.total) * 100));
            }
          },
        },
      );
      return asset;
    },
    onSuccess: (_, { jobId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.jobAssets(jobId) });
    },
  });
}

export function useGenerateHooks(): UseMutationResult<JobHook[], Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId) =>
      api.post<JobHook[]>(`/jobs/${jobId}/generate-hooks`).then((r) => r.data),
    onSuccess: (_, jobId) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.jobHooks(jobId) });
    },
  });
}

interface ApproveHookPayload {
  jobId: string;
  hookId: string;
  editedText?: string;
}

export function useApproveHook(): UseMutationResult<
  ContentJob,
  Error,
  ApproveHookPayload
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, hookId, editedText }) =>
      api
        .post<ContentJob>(`/jobs/${jobId}/approve-hook`, {
          hook_id: hookId,
          edited_text: editedText,
        })
        .then((r) => r.data),
    onSuccess: (_, { jobId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.jobHooks(jobId) });
    },
  });
}

interface SelectDestinationsPayload {
  jobId: string;
  socialAccountIds: string[];
}

export function useSelectDestinations(): UseMutationResult<
  ContentJob,
  Error,
  SelectDestinationsPayload
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, socialAccountIds }) =>
      api
        .post<ContentJob>(`/jobs/${jobId}/select-destinations`, {
          social_account_ids: socialAccountIds,
        })
        .then((r) => r.data),
    onSuccess: (_, { jobId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.publishTargets(jobId) });
    },
  });
}

export function usePublishNow(): UseMutationResult<
  PublishTarget[],
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId) =>
      api
        .post<PublishTarget[]>(`/jobs/${jobId}/publish-now`)
        .then((r) => r.data),
    onSuccess: (_, jobId) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.publishTargets(jobId) });
    },
  });
}

interface ScheduleJobPayload {
  jobId: string;
  scheduledAt: string;
  timezone: string;
}

export function useScheduleJob(): UseMutationResult<
  ContentJob,
  Error,
  ScheduleJobPayload
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, scheduledAt, timezone }) =>
      api
        .post<ContentJob>(`/jobs/${jobId}/schedule`, {
          scheduled_at_utc: scheduledAt,
          user_timezone: timezone,
        })
        .then((r) => r.data),
    onSuccess: (_, { jobId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.job(jobId) });
    },
  });
}

interface ConnectSocialPayload {
  platform: string;
  code: string;
  redirectUri: string;
}

export function useConnectSocial(): UseMutationResult<
  SocialAccount,
  Error,
  ConnectSocialPayload
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ platform, code, redirectUri }) =>
      api
        .post<SocialAccount>(`/social-accounts/connect/${platform}`, {
          code,
          redirect_uri: redirectUri,
        })
        .then((r) => r.data),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: queryKeys.socialAccounts }),
  });
}
