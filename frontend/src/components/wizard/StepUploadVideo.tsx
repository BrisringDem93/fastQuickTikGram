"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileVideo, X, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import type { ContentJob } from "@/types";
import { JobStatus } from "@/types";
import { useUploadVideo } from "@/lib/queries";
import { formatFileSize, getErrorMessage } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"];
const ACCEPTED_EXTENSIONS = ".mp4, .mov, .avi, .mkv";
const MAX_SIZE_BYTES = 500 * 1024 * 1024; // 500 MB

interface Props {
  job: ContentJob;
}

export function StepUploadVideo({ job }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadVideo();

  const alreadyUploaded =
    job.status !== JobStatus.PENDING_UPLOAD &&
    job.status !== JobStatus.UPLOAD_IN_PROGRESS;

  const validateAndSetFile = useCallback((f: File) => {
    if (!ACCEPTED_TYPES.includes(f.type)) {
      toast.error(`Unsupported format. Please use ${ACCEPTED_EXTENSIONS}.`);
      return;
    }
    if (f.size > MAX_SIZE_BYTES) {
      toast.error("File is too large. Maximum size is 500 MB.");
      return;
    }
    setFile(f);
    setProgress(0);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) validateAndSetFile(dropped);
    },
    [validateAndSetFile],
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0];
    if (picked) validateAndSetFile(picked);
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      await uploadMutation.mutateAsync({
        jobId: job.id,
        file,
        onProgress: setProgress,
      });
      toast.success("Video uploaded successfully!");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  if (alreadyUploaded) {
    return (
      <div className="card p-8 text-center">
        <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-500" />
        <h2 className="text-lg font-semibold text-gray-900">Video uploaded</h2>
        <p className="mt-1 text-sm text-gray-500">
          Your video has been uploaded successfully. Proceed to the next step.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-8">
      <h2 className="mb-1 text-xl font-bold text-gray-900">Upload your video</h2>
      <p className="mb-6 text-sm text-gray-500">
        Accepted formats: {ACCEPTED_EXTENSIONS} · Max size: 500 MB
      </p>

      {/* Drop zone */}
      {!file && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-16 transition-colors",
            dragging
              ? "border-brand-500 bg-brand-50"
              : "border-gray-300 bg-gray-50 hover:border-brand-400 hover:bg-brand-50/40",
          )}
        >
          <UploadCloud
            className={cn(
              "h-12 w-12 transition-colors",
              dragging ? "text-brand-600" : "text-gray-400",
            )}
          />
          <div className="text-center">
            <p className="text-sm font-medium text-gray-700">
              Drag & drop your video here or{" "}
              <span className="text-brand-600">browse files</span>
            </p>
            <p className="mt-1 text-xs text-gray-400">
              {ACCEPTED_EXTENSIONS} — up to 500 MB
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      )}

      {/* File selected */}
      {file && (
        <div className="space-y-5">
          <div className="flex items-center gap-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
            <FileVideo className="h-8 w-8 shrink-0 text-brand-500" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-gray-900">
                {file.name}
              </p>
              <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
            </div>
            {!uploadMutation.isPending && (
              <button
                onClick={() => { setFile(null); setProgress(0); }}
                className="rounded p-1 hover:bg-gray-200"
              >
                <X className="h-4 w-4 text-gray-500" />
              </button>
            )}
          </div>

          {uploadMutation.isPending && (
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Uploading…</span>
                <span>{progress}%</span>
              </div>
              <ProgressBar value={progress} />
            </div>
          )}

          {uploadMutation.isSuccess && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              Upload complete
            </div>
          )}

          <div className="flex gap-3">
            <Button
              onClick={handleUpload}
              disabled={uploadMutation.isPending || uploadMutation.isSuccess}
              isLoading={uploadMutation.isPending}
            >
              {uploadMutation.isSuccess ? "Uploaded ✓" : "Upload Video"}
            </Button>
            {!uploadMutation.isPending && !uploadMutation.isSuccess && (
              <Button
                variant="outline"
                onClick={() => { setFile(null); setProgress(0); }}
              >
                Choose different file
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
