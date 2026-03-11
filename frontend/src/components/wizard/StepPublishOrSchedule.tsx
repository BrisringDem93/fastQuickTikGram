"use client";

import { useState } from "react";
import { format, addDays } from "date-fns";
import {
  CalendarClock,
  Send,
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
} from "lucide-react";
import toast from "react-hot-toast";
import type { ContentJob } from "@/types";
import { JobStatus } from "@/types";
import { usePublishNow, useScheduleJob, usePublishTargets } from "@/lib/queries";
import { Button } from "@/components/ui/Button";
import { PlatformIcon } from "@/components/ui/PlatformIcon";
import { getPlatformLabel, formatDate, getErrorMessage } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Platform } from "@/types";

interface Props {
  job: ContentJob;
}

type PublishMode = "now" | "schedule" | null;

function TargetStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "published":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "failed":
      return <XCircle className="h-5 w-5 text-red-500" />;
    case "in_progress":
      return <Loader2 className="h-5 w-5 animate-spin text-brand-500" />;
    default:
      return <Loader2 className="h-5 w-5 text-gray-300" />;
  }
}

export function StepPublishOrSchedule({ job }: Props) {
  const publishNow = usePublishNow();
  const scheduleJob = useScheduleJob();
  const { data: targets } = usePublishTargets(job.id);

  const [mode, setMode] = useState<PublishMode>(null);
  const [scheduledDate, setScheduledDate] = useState(
    format(addDays(new Date(), 1), "yyyy-MM-dd"),
  );
  const [scheduledTime, setScheduledTime] = useState("10:00");
  const [timezone] = useState(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone,
  );

  const isPublishing =
    job.status === JobStatus.PUBLISHING_IN_PROGRESS ||
    publishNow.isPending;

  const isPublished =
    job.status === JobStatus.PUBLISHED ||
    job.status === JobStatus.PARTIALLY_PUBLISHED;

  const isScheduled = job.status === JobStatus.SCHEDULED;

  const handlePublishNow = async () => {
    try {
      await publishNow.mutateAsync(job.id);
      toast.success("Publishing started!");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleSchedule = async () => {
    try {
      const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}:00`).toISOString();
      await scheduleJob.mutateAsync({ jobId: job.id, scheduledAt, timezone });
      toast.success("Job scheduled successfully!");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-1 text-xl font-bold text-gray-900">Publish</h2>
        <p className="text-sm text-gray-500">
          Choose when to publish your content to the selected platforms.
        </p>
      </div>

      {/* Publish targets summary */}
      {targets && targets.length > 0 && (
        <div className="card p-6">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">
            Publishing to
          </h3>
          <div className="space-y-3">
            {targets.map((t) => (
              <div key={t.id} className="flex items-center gap-3">
                <PlatformIcon platform={t.platform as Platform} size={28} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {getPlatformLabel(t.platform as Platform)}
                  </p>
                  {t.error_message && (
                    <p className="text-xs text-red-500">{t.error_message}</p>
                  )}
                  {t.published_at && (
                    <p className="text-xs text-gray-400">
                      Published {formatDate(t.published_at, "MMM d 'at' h:mm a")}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <TargetStatusIcon status={t.status} />
                  {t.external_post_url && (
                    <a
                      href={t.external_post_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-brand-600"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scheduled state */}
      {isScheduled && job.scheduled_at_utc && (
        <div className="card flex items-center gap-4 p-6 bg-blue-50 border-blue-200">
          <CalendarClock className="h-8 w-8 text-blue-500 shrink-0" />
          <div>
            <p className="font-semibold text-blue-900">Job Scheduled</p>
            <p className="text-sm text-blue-600">
              Scheduled for{" "}
              {formatDate(job.scheduled_at_utc, "EEEE, MMMM d 'at' h:mm a")}
              {job.user_timezone ? ` (${job.user_timezone})` : ""}
            </p>
          </div>
        </div>
      )}

      {/* Published state */}
      {isPublished && (
        <div className="card flex items-center gap-4 p-6 bg-green-50 border-green-200">
          <CheckCircle className="h-8 w-8 text-green-500 shrink-0" />
          <div>
            <p className="font-semibold text-green-900">
              {job.status === JobStatus.PUBLISHED
                ? "Successfully Published!"
                : "Partially Published"}
            </p>
            <p className="text-sm text-green-600">
              Your content has been published to the selected platforms.
            </p>
          </div>
        </div>
      )}

      {/* Action buttons */}
      {!isScheduled && !isPublished && (
        <div className="card p-6 space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Publish now */}
            <button
              onClick={() => setMode("now")}
              className={cn(
                "flex flex-col items-center gap-3 rounded-xl border-2 p-6 text-center transition",
                mode === "now"
                  ? "border-brand-500 bg-brand-50"
                  : "border-gray-200 bg-white hover:border-brand-300",
              )}
            >
              <Send className={`h-7 w-7 ${mode === "now" ? "text-brand-600" : "text-gray-400"}`} />
              <div>
                <p className="font-semibold text-gray-900">Publish Now</p>
                <p className="text-xs text-gray-500 mt-1">
                  Immediately publish to all selected platforms
                </p>
              </div>
            </button>

            {/* Schedule */}
            <button
              onClick={() => setMode("schedule")}
              className={cn(
                "flex flex-col items-center gap-3 rounded-xl border-2 p-6 text-center transition",
                mode === "schedule"
                  ? "border-brand-500 bg-brand-50"
                  : "border-gray-200 bg-white hover:border-brand-300",
              )}
            >
              <CalendarClock className={`h-7 w-7 ${mode === "schedule" ? "text-brand-600" : "text-gray-400"}`} />
              <div>
                <p className="font-semibold text-gray-900">Schedule</p>
                <p className="text-xs text-gray-500 mt-1">
                  Pick a date and time to publish automatically
                </p>
              </div>
            </button>
          </div>

          {/* Schedule inputs */}
          {mode === "schedule" && (
            <div className="space-y-4 rounded-xl border border-gray-200 p-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-gray-700">
                    Date
                  </label>
                  <input
                    type="date"
                    value={scheduledDate}
                    min={format(new Date(), "yyyy-MM-dd")}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="input-base"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-gray-700">
                    Time
                  </label>
                  <input
                    type="time"
                    value={scheduledTime}
                    onChange={(e) => setScheduledTime(e.target.value)}
                    className="input-base"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-400">
                Your timezone: <strong>{timezone}</strong>
              </p>
            </div>
          )}

          {/* Action button */}
          {mode && (
            <div className="flex justify-end">
              {mode === "now" ? (
                <Button
                  onClick={handlePublishNow}
                  disabled={isPublishing}
                  isLoading={isPublishing}
                >
                  <Send className="h-4 w-4" />
                  {isPublishing ? "Publishing…" : "Publish Now"}
                </Button>
              ) : (
                <Button
                  onClick={handleSchedule}
                  disabled={scheduleJob.isPending || !scheduledDate || !scheduledTime}
                  isLoading={scheduleJob.isPending}
                >
                  <CalendarClock className="h-4 w-4" />
                  Confirm Schedule
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
