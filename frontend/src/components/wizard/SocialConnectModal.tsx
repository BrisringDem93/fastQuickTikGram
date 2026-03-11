"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { X, CheckCircle, Loader2, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";
import { useSocialAccounts } from "@/lib/queries";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { PlatformIcon } from "@/components/ui/PlatformIcon";
import { Platform } from "@/types";
import { getPlatformLabel } from "@/lib/utils";

interface Props {
  onClose: () => void;
  jobId: string;
}

const PLATFORMS = [
  Platform.youtube,
  Platform.tiktok,
  Platform.instagram,
  Platform.facebook,
];

const PLATFORM_OAUTH_URLS: Record<Platform, string> = {
  [Platform.youtube]: "/api/social-accounts/oauth/youtube",
  [Platform.tiktok]: "/api/social-accounts/oauth/tiktok",
  [Platform.instagram]: "/api/social-accounts/oauth/instagram",
  [Platform.facebook]: "/api/social-accounts/oauth/facebook",
};

export function SocialConnectModal({ onClose, jobId }: Props) {
  const { data: accounts, refetch, isRefetching } = useSocialAccounts();
  const [connecting, setConnecting] = useState<Platform | null>(null);
  const popupRef = useRef<Window | null>(null);

  const connectedPlatforms = new Set(
    accounts?.filter((a) => a.is_active).map((a) => a.platform) ?? [],
  );
  const hasConnected = connectedPlatforms.size > 0;

  // Listen for OAuth popup message
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      if (event.data?.type === "oauth_success") {
        setConnecting(null);
        refetch();
        toast.success(`${event.data.platform ?? "Account"} connected!`);
        popupRef.current?.close();
      } else if (event.data?.type === "oauth_error") {
        setConnecting(null);
        toast.error(event.data.message ?? "Failed to connect account.");
        popupRef.current?.close();
      }
    },
    [refetch],
  );

  useEffect(() => {
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [handleMessage]);

  // Poll for popup closure (user closed without completing)
  useEffect(() => {
    if (!connecting) return;
    const interval = setInterval(() => {
      if (popupRef.current?.closed) {
        setConnecting(null);
        clearInterval(interval);
      }
    }, 500);
    return () => clearInterval(interval);
  }, [connecting]);

  const handleConnect = (platform: Platform) => {
    const url = `${PLATFORM_OAUTH_URLS[platform]}?job_id=${jobId}`;
    const popup = window.open(
      url,
      `connect_${platform}`,
      "width=600,height=700,left=200,top=100",
    );
    if (!popup) {
      toast.error("Pop-up blocked. Please allow pop-ups for this site.");
      return;
    }
    popupRef.current = popup;
    setConnecting(platform);
  };

  return (
    <Modal onClose={onClose} title="Connect Social Accounts">
      <div className="space-y-4">
        <p className="text-sm text-gray-500">
          Connect your social media accounts to publish your content. You can
          always add more accounts later.
        </p>

        <div className="space-y-3">
          {PLATFORMS.map((platform) => {
            const isConnected = connectedPlatforms.has(platform);
            const isConnecting = connecting === platform;
            return (
              <div
                key={platform}
                className="flex items-center justify-between rounded-xl border border-gray-200 p-4"
              >
                <div className="flex items-center gap-3">
                  <PlatformIcon platform={platform} size={32} />
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {getPlatformLabel(platform)}
                    </p>
                    {isConnected && (
                      <p className="text-xs text-green-600">Connected</p>
                    )}
                  </div>
                </div>
                {isConnected ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleConnect(platform)}
                    disabled={!!connecting}
                    isLoading={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Connecting…
                      </>
                    ) : (
                      <>
                        <ExternalLink className="h-3.5 w-3.5" />
                        Connect
                      </>
                    )}
                  </Button>
                )}
              </div>
            );
          })}
        </div>

        {isRefetching && (
          <p className="text-center text-xs text-gray-400">
            Refreshing accounts…
          </p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" onClick={onClose}>
            <X className="h-4 w-4" />
            Cancel
          </Button>
          <Button
            onClick={onClose}
            disabled={!hasConnected}
          >
            <CheckCircle className="h-4 w-4" />
            Continue to Publishing
          </Button>
        </div>
      </div>
    </Modal>
  );
}
