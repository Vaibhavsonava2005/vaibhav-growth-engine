/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://vaibhav-growth-engine-api.onrender.com/api/:path*',
      },
    ]
  },
}
export default nextConfig
