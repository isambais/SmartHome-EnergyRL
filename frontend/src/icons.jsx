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
export const Moon = (p) => <S {...p}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></S>;
export const Mail = (p) => <S {...p}><rect x="2" y="5" width="20" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></S>;
export const ArrowUp = (p) => <S {...p}><path d="M12 19V5M6 11l6-6 6 6" /></S>;
export const Github = ({ size = 22, ...p }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.09.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.37-3.37-1.37-.45-1.18-1.11-1.49-1.11-1.49-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.55-1.14-4.55-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.81-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.02 10.02 0 0 0 22 12.25C22 6.58 17.52 2 12 2z" />
  </svg>
);
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
export const Calendar = (p) => <S {...p}><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M8 2v4M16 2v4M3 10h18" /></S>;
export const User = (p) => <S {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-6.5 8-6.5s8 2.5 8 6.5" /></S>;
export const Lock = (p) => <S {...p}><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></S>;
export const Building = (p) => <S {...p}><rect x="5" y="3" width="14" height="18" rx="1.5" /><path d="M3 21h18M9 7h.01M15 7h.01M9 11h.01M15 11h.01M9 15h.01M15 15h.01" /></S>;
export const Star = ({ size = 18, ...p }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8L12 2z" />
  </svg>
);
