const families: Record<string, [string, string, string, string]> = {
  cocoa: ["#3B2418", "#C4A574", "#E7D7C1", "#D6F25C"],
  nut: ["#8C5A2A", "#E0A045", "#F6E7C8", "#1A5240"],
  fruit: ["#9E3B3A", "#F0B7A8", "#FBF8F2", "#1A5240"],
  grain: ["#C4A574", "#E7D3A4", "#FBF8F2", "#1A5240"],
  seed: ["#2F4A38", "#C4A574", "#E7E1D4", "#D6F25C"],
};

export function ProductArt({ family, className = "" }: { family: string; className?: string }) {
  const [a, b, c, d] = families[family] || families.grain;
  return (
    <svg viewBox="0 0 360 460" className={className} role="img" aria-label={`${family} packaging concept`}>
      <rect width="360" height="460" rx="36" fill={a} />
      <circle cx="290" cy="70" r="46" fill={d} opacity="0.9" />
      <circle cx="64" cy="390" r="28" fill={b} />
      <g transform="translate(78 90)">
        <rect width="204" height="46" rx="16" fill={c} />
        <rect y="58" width="204" height="46" rx="16" fill={d} />
        <rect y="116" width="204" height="46" rx="16" fill={b} />
        <rect y="174" width="204" height="36" rx="14" fill={c} opacity="0.8" />
      </g>
      <text x="40" y="420" fill={c} fontFamily="Space Grotesk, sans-serif" fontSize="18" letterSpacing="3">CONCEPT</text>
    </svg>
  );
}

export function Mark({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="currentColor" />
      <rect x="7" y="8" width="18" height="4" rx="2" fill="#FBF8F2" />
      <rect x="7" y="14" width="18" height="4" rx="2" fill="#D6F25C" />
      <rect x="7" y="20" width="18" height="4" rx="2" fill="#E6D3A3" />
    </svg>
  );
}
