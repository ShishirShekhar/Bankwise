import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",

  reactStrictMode: true,
  typedRoutes: true,
  reactCompiler: true,

  images: {
    unoptimized: true,
    remotePatterns: [{ protocol: "https", hostname: "cdn.yourdomain.com" }],
  },

  experimental: {
    // optimizePackageImports: ["lucide-react", "date-fns"],
  },
};

export default nextConfig;
