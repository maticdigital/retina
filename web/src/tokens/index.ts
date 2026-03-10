/**
 * Retina Design System Tokens
 * -------------------------------------------------
 * Derived from the Streamlit styles.py + Dashboard Simple reference.
 * Will be replaced/augmented with Cabana Figma export tokens.
 */

/* ── Color Primitives ─────────────────────────────── */

export const color = {
  /* Backgrounds */
  bgPage: '#F0F2F5',
  bgCard: '#FFFFFF',
  bgHover: '#EDF0F7',

  /* Accent */
  accent: '#000227',
  accentHover: '#076EFF',
  accentLight: '#E8F0FF',

  /* Text */
  text: '#0A0A2E',
  textMuted: '#6B7280',
  textDim: '#94A3B8',
  textOnAccent: '#FFFFFF',

  /* Status */
  success: '#00C864',
  warning: '#FFC800',
  error: '#FF4444',

  /* Borders / Shadows */
  border: '#E2E8F0',
  shadow: '0 1px 4px rgba(0,0,0,0.06)',
  shadowMd: '0 2px 8px rgba(0,0,0,0.08)',

  /* Lens palette */
  lensPerformance: '#076EFF',
  lensSeo: '#00C864',
  lensBrand: '#9B59B6',
  lensExperience: '#E74C3C',
  lensConversion: '#FF8C00',
} as const;

/* ── Typography ───────────────────────────────────── */

export const font = {
  family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  sizeXs: '0.75rem',   // 12px
  sizeSm: '0.8125rem',  // 13px
  sizeBase: '0.875rem', // 14px
  sizeMd: '1rem',       // 16px
  sizeLg: '1.25rem',    // 20px
  sizeXl: '1.5rem',     // 24px
  size2xl: '2rem',      // 32px
  weightRegular: 400,
  weightMedium: 500,
  weightSemibold: 600,
  weightBold: 700,
} as const;

/* ── Spacing ──────────────────────────────────────── */

export const space = {
  xxs: '0.25rem',  // 4px
  xs: '0.5rem',    // 8px
  sm: '0.75rem',   // 12px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  xxl: '3rem',     // 48px
} as const;

/* ── Radii ────────────────────────────────────────── */

export const radius = {
  sm: '6px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  pill: '999px',
} as const;

/* ── Sidebar ──────────────────────────────────────── */

export const sidebar = {
  width: '200px',
  bgColor: '#FFFFFF',
} as const;
