import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output — reduces node_modules in production
  output: "standalone",


  // Proxy API calls to FastAPI backend (:8000)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },

  // Bundle optimization: tree-shake unused deps
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "framer-motion",
      "radix-ui",
      "react-bits",
    ],
  },

  // Keep source maps manageable
  productionBrowserSourceMaps: false,
};

export default nextConfig;
