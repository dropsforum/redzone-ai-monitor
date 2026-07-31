import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  /* config options here */
  async headers() {
    const experimentalIsolationHeaders = process.env.ENABLE_CROSS_ORIGIN_ISOLATION === '1'
      ? [
          { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
          { key: 'Cross-Origin-Embedder-Policy', value: 'require-corp' },
        ]
      : [];
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "frame-ancestors 'self' https://www.dropsforum.org https://dropsforum.org;",
          },
          ...experimentalIsolationHeaders,
        ],
      },
    ];
  },
  webpack: (config) => {
    // Fixes npm packages that depend on `fs` module
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
    };
    config.module.rules.push({
      test: /@ultralytics[\\/]yolo[\\/]dist[\\/]index\.js$/,
      use: [{
        loader: path.resolve(process.cwd(), "scripts/ultralytics-yolo-next-loader.cjs"),
      }],
    });

    return config;
  },
};

export default nextConfig;
