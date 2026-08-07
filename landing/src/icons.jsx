/* Basit inline SVG ikonlar (Lucide tarzı, stroke tabanlı) */
const S = ({ children, size = 22, ...p }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...p}>
    {children}
  </svg>
);

export const Bolt = (p) => <S {...p}><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" /></S>;
export const Battery = (p) => <S {...p}><rect x="2" y="7" width="16" height="10" rx="2" /><path d="M22 11v2M6 11v2M10 11v2" /></S>;
export const Sun = (p) => <S {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></S>;
export const Chart = (p) => <S {...p}><path d="M3 3v18h18" /><path d="M7 15l4-6 4 3 5-8" /></S>;
export const Home = (p) => <S {...p}><path d="M3 10 12 3l9 7" /><path d="M5 9v11h14V9" /></S>;
export const Shield = (p) => <S {...p}><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3z" /></S>;
export const Brain = (p) => <S {...p}><circle cx="12" cy="12" r="9" /><path d="M12 3v18M12 8c-3 0-5 1.8-5 4M12 8c3 0 5 1.8 5 4" /></S>;
export const Alert = (p) => <S {...p}><path d="M12 3 2 20h20L12 3z" /><path d="M12 10v4M12 17.5v.5" /></S>;
export const Coins = (p) => <S {...p}><circle cx="9" cy="9" r="6" /><path d="M14.5 5.3A6 6 0 1 1 8 18.7" /></S>;
export const Check = (p) => <S size={16} {...p}><path d="M20 6 9 17l-5-5" /></S>;
export const X = (p) => <S size={16} {...p}><path d="M18 6 6 18M6 6l12 12" /></S>;
export const Arrow = (p) => <S size={18} {...p}><path d="M5 12h14M13 6l6 6-6 6" /></S>;
export const Chevron = (p) => <S size={18} {...p}><path d="m6 9 6 6 6-6" /></S>;
export const Cube = (p) => <S {...p}><path d="M12 2 3 7v10l9 5 9-5V7l-9-5z" /><path d="M3 7l9 5 9-5M12 12v10" /></S>;
export const Gauge = (p) => <S {...p}><path d="M12 21a9 9 0 1 1 9-9" /><path d="M12 12l5-3" /></S>;
export const Star = ({ size = 18, ...p }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8L12 2z" />
  </svg>
);
