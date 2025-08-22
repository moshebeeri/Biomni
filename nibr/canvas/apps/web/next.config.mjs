/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable SWC minification for faster builds
  swcMinify: true,
  
  // Disable source maps in production
  productionBrowserSourceMaps: false,
  
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.output.globalObject = 'self';
    }
    
    // Handle Node.js modules in client builds
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        crypto: false,
        stream: false,
        util: false,
        buffer: false,
      };
    }
    
    // Ignore source map warnings
    config.ignoreWarnings = [
      { module: /node_modules/ },
      {
        message: /source-map-loader/,
      },
    ];
    
    return config;
  },
};

export default nextConfig;
