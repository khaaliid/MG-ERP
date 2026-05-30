export const APP_CONFIG = {
  ads: {
    // Central ad endpoint config for backend/public ad payloads.
    publicAdsApiUrl: (import.meta as any).env?.VITE_PUBLIC_ADS_API_URL || 'https://dummyjson.com/posts/1'
  }
};
