import { cn } from "@/lib/utils";
import { Platform } from "@/types";
import { Youtube, Music2, Instagram, Facebook } from "lucide-react";

interface PlatformIconProps {
  platform: Platform;
  size?: number;
  className?: string;
  showLabel?: boolean;
}

const PLATFORM_STYLES: Record<
  Platform,
  { bg: string; fg: string; icon: React.ElementType }
> = {
  [Platform.youtube]: {
    bg: "bg-red-100",
    fg: "text-red-600",
    icon: Youtube,
  },
  [Platform.tiktok]: {
    bg: "bg-gray-900",
    fg: "text-white",
    icon: Music2,
  },
  [Platform.instagram]: {
    bg: "bg-gradient-to-br from-pink-400 via-purple-400 to-orange-400",
    fg: "text-white",
    icon: Instagram,
  },
  [Platform.facebook]: {
    bg: "bg-blue-600",
    fg: "text-white",
    icon: Facebook,
  },
};

const PLATFORM_LABELS: Record<Platform, string> = {
  [Platform.youtube]: "YouTube",
  [Platform.tiktok]: "TikTok",
  [Platform.instagram]: "Instagram",
  [Platform.facebook]: "Facebook",
};

export function PlatformIcon({
  platform,
  size = 36,
  className,
  showLabel = false,
}: PlatformIconProps) {
  const style = PLATFORM_STYLES[platform];
  if (!style) return null;

  const Icon = style.icon;
  const iconSize = Math.round(size * 0.55);
  const borderRadius = Math.round(size * 0.25);

  return (
    <div className={cn("inline-flex flex-col items-center gap-1", className)}>
      <div
        className={cn(
          "flex items-center justify-center shrink-0",
          style.bg,
          style.fg,
        )}
        style={{ width: size, height: size, borderRadius }}
        title={PLATFORM_LABELS[platform]}
        aria-label={PLATFORM_LABELS[platform]}
      >
        <Icon style={{ width: iconSize, height: iconSize }} />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-gray-600">
          {PLATFORM_LABELS[platform]}
        </span>
      )}
    </div>
  );
}
