"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import type { ContentJob } from "@/types";
import { useJobHooks, useApproveHook } from "@/lib/queries";
import { Button } from "@/components/ui/Button";
import { getErrorMessage } from "@/lib/utils";

interface Props {
  job: ContentJob;
}

export function StepApproveHook({ job }: Props) {
  const { data: hooks } = useJobHooks(job.id);
  const approveMutation = useApproveHook();

  const selectedHook = hooks?.find((h) => h.is_selected) ?? null;
  const [hookText, setHookText] = useState(selectedHook?.text ?? "");
  const [isEdited, setIsEdited] = useState(false);

  useEffect(() => {
    if (selectedHook && !isEdited) {
      setHookText(selectedHook.text);
    }
  }, [selectedHook, isEdited]);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setHookText(e.target.value);
    setIsEdited(e.target.value !== (selectedHook?.text ?? ""));
  };

  const handleApprove = async () => {
    if (!selectedHook) return;
    try {
      await approveMutation.mutateAsync({
        jobId: job.id,
        hookId: selectedHook.id,
        editedText: isEdited ? hookText : undefined,
      });
      toast.success("Hook approved! Now select your publishing platforms.");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleBackToSelection = async () => {
    // Just navigate back — the job status controls which step renders.
    // We clear the hook selection by re-generating or user can regenerate on step 2.
    toast("Select a different hook on the previous step.", { icon: "ℹ️" });
  };

  if (!selectedHook) {
    return (
      <div className="card p-8 text-center">
        <p className="text-sm text-gray-500">
          No hook selected yet. Go back to step 2 and select a hook first.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-1 text-xl font-bold text-gray-900">Review Your Hook</h2>
        <p className="text-sm text-gray-500">
          You can edit the hook text below before approving. Your changes will be
          saved alongside the original AI suggestion.
        </p>
      </div>

      <div className="card p-6 space-y-4">
        <label className="block text-sm font-semibold text-gray-900">
          Hook text
        </label>
        <textarea
          value={hookText}
          onChange={handleTextChange}
          rows={5}
          className="input-base resize-none"
          placeholder="Enter your hook text…"
          maxLength={500}
        />
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>{hookText.length}/500 characters</span>
          {isEdited && (
            <span className="flex items-center gap-1 text-amber-600">
              <AlertTriangle className="h-3.5 w-3.5" />
              Modified from original AI suggestion
            </span>
          )}
        </div>

        {isEdited && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
            <strong>Note:</strong> You've edited the original AI suggestion. The
            edited version will be used for publishing.
          </div>
        )}
      </div>

      {/* Original hook (if edited) */}
      {isEdited && (
        <div className="card p-4">
          <p className="mb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Original AI suggestion
          </p>
          <p className="text-sm text-gray-600 italic">{selectedHook.text}</p>
        </div>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleApprove}
          disabled={!hookText.trim() || approveMutation.isPending}
          isLoading={approveMutation.isPending}
        >
          <CheckCircle className="h-4 w-4" />
          Approve Hook
        </Button>
        <Button variant="outline" onClick={handleBackToSelection}>
          <ArrowLeft className="h-4 w-4" />
          Back to Selection
        </Button>
      </div>
    </div>
  );
}
