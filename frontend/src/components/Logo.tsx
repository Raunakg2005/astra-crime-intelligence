// Astra mark — a shield (protection / police) holding a small constellation-network
// (linked intelligence) with a glowing hotspot node. Self-contained SVG, dark-friendly.
export default function Logo({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="astra-g" x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22d3ee" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
        <radialGradient id="astra-glow" cx="0.5" cy="0.5" r="0.5">
          <stop stopColor="#f43f5e" stopOpacity="0.9" />
          <stop offset="1" stopColor="#f43f5e" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* shield */}
      <path
        d="M24 3.5l14 4.6v10.4c0 9.4-6 16.4-14 20-8-3.6-14-10.6-14-20V8.1L24 3.5z"
        fill="#0b1120"
        stroke="url(#astra-g)"
        strokeWidth="2"
        strokeLinejoin="round"
      />

      {/* network edges */}
      <g stroke="url(#astra-g)" strokeWidth="1.7" strokeLinecap="round" opacity="0.95">
        <path d="M24 14L15 24" />
        <path d="M24 14L33 24" />
        <path d="M15 24L24 33" />
        <path d="M33 24L24 33" />
        <path d="M15 24L33 24" />
      </g>

      {/* hotspot glow */}
      <circle cx="24" cy="33" r="9" fill="url(#astra-glow)" />

      {/* nodes */}
      <circle cx="15" cy="24" r="2.7" fill="#38bdf8" />
      <circle cx="33" cy="24" r="2.7" fill="#22d3ee" />
      <circle cx="24" cy="33" r="3.1" fill="#f43f5e" />

      {/* star (astra) at the apex */}
      <path
        d="M24 8.5l1.7 3.6 3.9.5-2.9 2.7.8 3.9-3.5-2-3.5 2 .8-3.9-2.9-2.7 3.9-.5L24 8.5z"
        fill="#e0f2fe"
      />
    </svg>
  );
}
