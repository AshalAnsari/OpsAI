/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingIncludes: {
    "/policies/[slug]": ["./content/policies/**/*"],
  },
};

module.exports = nextConfig;
