import { sanitizeExternalUrl } from "../security/url";

export function SafeImage({ src, alt, className, loading = "lazy" }) {
  const safeSrc = sanitizeExternalUrl(src);
  if (!safeSrc) return null;

  return (
    <img
      src={safeSrc}
      alt={alt}
      className={className}
      loading={loading}
      referrerPolicy="no-referrer"
    />
  );
}

export function SafeVideo({ src, className }) {
  const safeSrc = sanitizeExternalUrl(src);
  if (!safeSrc) return null;

  return (
    <video
      controls
      src={safeSrc}
      className={className}
      preload="metadata"
      referrerPolicy="no-referrer"
    />
  );
}
