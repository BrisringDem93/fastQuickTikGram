"use client";

import { Sparkles, RefreshCw, Star, CheckCircle, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import type { ContentJob, JobHook } from "@/types";
import { JobStatus } from "@/types";
import { useGenerateHooks, useJobHooks, useApproveHook } from "@/lib/queries";
import { Button } from "@/components/ui/Button";
import { getErrorMessage } from "@/lib/utils";

interface Props {
  job: ContentJob;
}

function StarRating({ score }: { score: number }) {
  const stars = Math.round(score * 5);
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${i < stars ? "fill-yellow-400 text-yellow-400" : "fill-gray-200 text-gray-200"}`}
        />
      ))}
      <span className="ml-1.5 text-xs font-medium text-gray-500">
        {(score * 10).toFixed(1)}/10
      </span>
    </div>
  );
}

function HookCard({ hook, onSelect, isSelecting }: {
  hook: JobHook;
  onSelect: (_id: string) => void;
  isSelecting: boolean;
}) {
  return (
    <div className={`card flex flex-col gap-4 p-6 transition ${hook.is_selected ? "ring-2 ring-brand-500" : ""}`}>
      <div className="flex items-start justify-between gap-4">
        <p className="flex-1 text-sm font-medium leading-relaxed text-gray-900">
          {hook.text}
        </p>
        {hook.is_selected && (
          <CheckCircle className="h-5 w-5 shrink-0 text-brand-600" />
        )}
      </div>

      {hook.rationale && (
        <p className="rounded-lg bg-gray-50 p-3 text-xs leading-relaxed text-gray-500 italic">
          {hook.rationale}
        </p>
      )}

      <div className="flex items-center justify-between">
        <StarRating score={hook.score} />
        <Button
          size="sm"
          variant={hook.is_selected ? "secondary" : "primary"}
          onClick={() => onSelect(hook.id)}
          disabled={isSelecting}
        >
          {hook.is_selected ? "Selected ✓" : "Select This Hook"}
        </Button>
      </div>
    </div>
  );
}

const POLLING_STATUSES = [
  JobStatus.TRANSCRIPTION_IN_PROGRESS,
  JobStatus.HOOK_GENERATION_IN_PROGRESS,
];

export function StepGenerateHooks({ job }: Props) {
  const generateMutation = useGenerateHooks();
  const approveMutation = useApproveHook();
  const { data: hooks, isLoading: hooksLoading } = useJobHooks(job.id);

  const isPolling = POLLING_STATUSES.includes(job.status);
  const hooksReady =
    job.status === JobStatus.HOOK_GENERATION_COMPLETE ||
    job.status === JobStatus.HOOK_APPROVED ||
    (hooks && hooks.length > 0);

  const handleGenerate = async () => {
    try {
      await generateMutation.mutateAsync(job.id);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleSelect = async (hookId: string) => {
    try {
      await approveMutation.mutateAsync({ jobId: job.id, hookId });
      toast.success("Hook selected! Review and approve in the next step.");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">AI Hook Generator</h2>
            <p className="mt-1 text-sm text-gray-500">
              Our AI analyses your video transcript and generates hooks optimised
              for maximum engagement.
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            {hooksReady && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={generateMutation.isPending || isPolling}
              >
                <RefreshCw className="h-4 w-4" />
                Regenerate
              </Button>
            )}
            {!hooksReady && !isPolling && (
              <Button
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
                isLoading={generateMutation.isPending}
              >
                <Sparkles className="h-4 w-4" />
                Generate Hooks
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Loading / polling state */}
      {(isPolling || generateMutation.isPending) && (
        <div className="card flex flex-col items-center gap-4 py-16 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-brand-600" />
          <div>
            <p className="font-semibold text-gray-900">
              {job.status === JobStatus.TRANSCRIPTION_IN_PROGRESS
                ? "Transcribing your video…"
                : "AI is generating your hooks…"}
            </p>
            <p className="mt-1 text-sm text-gray-400">
              This usually takes 30–60 seconds. Hang tight!
            </p>
          </div>
        </div>
      )}

      {/* Hooks list */}
      {hooksReady && !isPolling && (
        <>
          {hooksLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="card h-36 animate-pulse bg-gray-50" />
              ))}
            </div>
          ) : hooks && hooks.length > 0 ? (
            <div className="space-y-4">
              {hooks
                .sort((a, b) => b.score - a.score)
                .map((hook) => (
                  <HookCard
                    key={hook.id}
                    hook={hook}
                    onSelect={handleSelect}
                    isSelecting={approveMutation.isPending}
                  />
                ))}
            </div>
          ) : (
            <div className="card p-8 text-center text-sm text-gray-500">
              No hooks generated yet. Click "Generate Hooks" to start.
            </div>
          )}
        </>
      )}

      {/* Initial empty state */}
      {!hooksReady && !isPolling && !generateMutation.isPending && (
        <div className="card flex flex-col items-center gap-4 py-16 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50">
            <Sparkles className="h-8 w-8 text-brand-400" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">Ready to generate hooks</p>
            <p className="mt-1 text-sm text-gray-400">
              Click "Generate Hooks" above to let the AI craft compelling openings
              for your video.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
