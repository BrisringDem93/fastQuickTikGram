"use client";

import { useState } from "react";
import { ExternalLink, PlusCircle, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import type { ContentJob } from "@/types";
import { useSocialAccounts, useSelectDestinations } from "@/lib/queries";
import { Button } from "@/components/ui/Button";
import { PlatformIcon } from "@/components/ui/PlatformIcon";
import { getPlatformLabel, getErrorMessage } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Platform } from "@/types";

interface Props {
  job: ContentJob;
  onOpenSocialModal: () => void;
}

export function StepSelectDestinations({ job, onOpenSocialModal }: Props) {
  const { data: accounts, isLoading } = useSocialAccounts();
  const selectMutation = useSelectDestinations();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const activeAccounts = accounts?.filter((a) => a.is_active) ?? [];

  const toggleAccount = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleContinue = async () => {
    if (selectedIds.size === 0) {
      toast.error("Please select at least one platform to publish to.");
      return;
    }
    try {
      await selectMutation.mutateAsync({
        jobId: job.id,
        socialAccountIds: Array.from(selectedIds),
      });
      toast.success("Destinations saved! Proceed to publish.");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Select Platforms</h2>
            <p className="mt-1 text-sm text-gray-500">
              Choose which connected accounts to publish this video to.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={onOpenSocialModal}>
            <PlusCircle className="h-4 w-4" />
            Connect Account
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card h-20 animate-pulse bg-gray-50" />
          ))}
        </div>
      ) : activeAccounts.length === 0 ? (
        <div className="card flex flex-col items-center gap-4 py-16 text-center">
          <p className="font-semibold text-gray-900">No connected accounts</p>
          <p className="text-sm text-gray-500">
            Connect at least one social account to continue.
          </p>
          <Button onClick={onOpenSocialModal}>
            <PlusCircle className="h-4 w-4" />
            Connect a Social Account
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {activeAccounts.map((account) => {
            const isSelected = selectedIds.has(account.id);
            return (
              <button
                key={account.id}
                onClick={() => toggleAccount(account.id)}
                className={cn(
                  "card w-full flex items-center gap-4 p-4 text-left transition",
                  isSelected
                    ? "ring-2 ring-brand-500 bg-brand-50/30"
                    : "hover:shadow-md hover:-translate-y-0.5",
                )}
              >
                <PlatformIcon
                  platform={account.platform as Platform}
                  size={32}
                  className="shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-gray-900">
                    {getPlatformLabel(account.platform as Platform)}
                  </p>
                  <p className="text-xs text-gray-400">@{account.account_name}</p>
                </div>
                {isSelected && (
                  <CheckCircle className="h-5 w-5 shrink-0 text-brand-600" />
                )}
              </button>
            );
          })}
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {selectedIds.size} account{selectedIds.size !== 1 ? "s" : ""} selected
        </p>
        <div className="flex gap-3">
          <Button variant="outline" size="sm" onClick={onOpenSocialModal}>
            <ExternalLink className="h-4 w-4" />
            Manage accounts
          </Button>
          <Button
            onClick={handleContinue}
            disabled={selectedIds.size === 0 || selectMutation.isPending}
            isLoading={selectMutation.isPending}
          >
            Continue →
          </Button>
        </div>
      </div>
    </div>
  );
}
