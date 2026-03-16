/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Disable the Next.js reverse-proxy timeout for large file uploads.
  // The default (5 seconds) would abort multipart video uploads routed
  // through the /api rewrite before the backend has finished receiving the body.
  experimental: {
    proxyTimeout: false,
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.googleapis.com" },
      { protocol: "https", hostname: "**.googleusercontent.com" },
      { protocol: "https", hostname: "**.tiktokcdn.com" },
      { protocol: "https", hostname: "**.cdninstagram.com" },
      { protocol: "https", hostname: "**.fbcdn.net" },
      { protocol: "https", hostname: "**.s3.amazonaws.com" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://backend:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
