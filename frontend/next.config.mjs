const backend = process.env.API_ORIGIN || 'http://127.0.0.1:8000';
export default {
  poweredByHeader: false,
  devIndicators: false,
  async rewrites() { return [{source: '/api/:path*', destination: `${backend}/api/:path*`}]; },
  async headers() { return [{source:'/:path*', headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'same-origin'},{key:'X-Frame-Options',value:'DENY'}]}]; }
};
