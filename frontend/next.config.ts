import { createMDX } from "fumadocs-mdx/next";
import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, ".."),
  poweredByHeader: false,
};

export default createMDX()(nextConfig);
