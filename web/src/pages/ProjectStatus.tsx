import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProjectStatus, retryPipeline, type PipelineStatus } from '../api';
import { useAuth } from '../context/AuthContext';
import { Sidebar } from '../components/Sidebar';
import { NAV_ITEMS } from './Dashboard';
import { color, font, space, radius } from '../tokens';

/* ── Step definitions ──────────────────────────────────── */

const STEPS = [
  { key: 'lighthouse', label: 'Collecting performance data' },
  { key: 'screenshots', label: 'Capturing screenshots' },
  { key: 'scoring', label: 'Calculating scores' },
  { key: 'ai_interpretation', label: 'Generating AI insights' },
  { key: 'analyst_seeding', label: 'Seeding analyst evaluations' },
  { key: 'complete', label: 'Analysis complete' },
] as const;

const STEP_KEYS = STEPS.map((s) => s.key);

function stepIndex(step: string): number {
  const idx = STEP_KEYS.indexOf(step as typeof STEP_KEYS[number]);
  return idx >= 0 ? idx : -1;
}

/* ── Lens icon data ────────────────────────────────────── */

interface LensIcon {
  id: string;
  name: string;
  color: string;
  activateAfter: string; // step key after which this lens activates
}

const LENS_ICONS: LensIcon[] = [
  { id: 'performance', name: 'Performance', color: color.lensPerformance, activateAfter: 'lighthouse' },
  { id: 'seo', name: 'SEO', color: color.lensSeo, activateAfter: 'screenshots' },
  { id: 'brand', name: 'Brand', color: color.lensBrand, activateAfter: 'ai_interpretation' },
  { id: 'experience', name: 'Experience', color: color.lensExperience, activateAfter: 'analyst_seeding' },
  { id: 'conversion', name: 'Conversion', color: color.lensConversion, activateAfter: 'complete' },
];

/* ── SVG lens icons (same as LensDetail page) ─────────── */

const LENS_SVGS: Record<string, React.ReactNode> = {
  performance: (
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
      <circle cx="20" cy="20" r="16" stroke="currentColor" strokeWidth="2" fill="none" />
      <path d="M20 10 L20 20 L28 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  seo: (
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
      <circle cx="18" cy="18" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
      <line x1="26" y1="26" x2="34" y2="34" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  brand: (
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
      <circle cx="20" cy="20" r="16" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="20" cy="20" r="8" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="20" cy="20" r="2" fill="currentColor" />
    </svg>
  ),
  experience: (
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
      <rect x="6" y="10" width="28" height="20" rx="3" stroke="currentColor" strokeWidth="2" fill="none" />
      <line x1="6" y1="16" x2="34" y2="16" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),
  conversion: (
    <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
      <path d="M8 32 L16 18 L24 24 L32 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="32" cy="8" r="3" fill="currentColor" />
    </svg>
  ),
};

/* ── Status icons ──────────────────────────────────────── */

function SpinnerIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" style={{ animation: 'spin 1s linear infinite' }}>
      <circle cx="10" cy="10" r="8" stroke={color.border} strokeWidth="2.5" fill="none" />
      <path d="M10 2 A8 8 0 0 1 18 10" stroke={color.lensPerformance} strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill={color.success} />
      <path d="M6 10 L9 13 L14 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill={color.error} />
      <path d="M7 7 L13 13 M13 7 L7 13" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function PendingIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="8" stroke={color.border} strokeWidth="2" fill="none" />
    </svg>
  );
}

/* ── Main Component ────────────────────────────────────── */

export default function ProjectStatus() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Poll for status
  useEffect(() => {
    if (!projectId) return;

    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getProjectStatus(projectId);
        if (!cancelled) {
          setStatus(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch status');
        }
      }
    };

    // Initial fetch
    poll();

    // Poll every 3 seconds while still running
    const interval = setInterval(poll, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [projectId]);

  // Auto-redirect when complete
  useEffect(() => {
    if (status?.status === 'complete' && !redirectTimerRef.current) {
      redirectTimerRef.current = setTimeout(() => {
        navigate(`/projects/${projectId}`);
      }, 1500);
    }
    // No cleanup — let the redirect fire even if component re-renders
  }, [status?.status, navigate, projectId]);

  const handleRetry = async () => {
    if (!projectId) return;
    setRetrying(true);
    try {
      const data = await retryPipeline(projectId);
      setStatus(data);
      setError(null);
      redirectTimerRef.current = null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Retry failed');
    } finally {
      setRetrying(false);
    }
  };

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const currentStep = status?.current_step ?? 'queued';
  const currentStepIdx = stepIndex(currentStep);
  const progress = status?.progress ?? 0;
  const isComplete = status?.status === 'complete';
  const isError = status?.status === 'error';

  return (
    <div style={styles.layout}>
      <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
      <main style={styles.main}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <span style={styles.headerLabel}>Project</span>
            <span style={styles.headerDivider}>|</span>
            <span style={styles.headerLabel}>Analyzing…</span>
          </div>
        </div>

        {/* Status Card */}
        <div style={styles.card}>
          {/* Lens icon row */}
          <div style={styles.lensRow}>
            {LENS_ICONS.map((lens) => {
              const activateIdx = stepIndex(lens.activateAfter);
              const isActive = currentStepIdx >= activateIdx && activateIdx >= 0;
              return (
                <div key={lens.id} style={styles.lensItem}>
                  <div
                    style={{
                      ...styles.lensIcon,
                      color: isActive ? lens.color : color.border,
                      opacity: isActive ? 1 : 0.4,
                      transition: 'color 0.5s, opacity 0.5s',
                    }}
                  >
                    {LENS_SVGS[lens.id]}
                  </div>
                  <span
                    style={{
                      ...styles.lensLabel,
                      color: isActive ? color.text : color.textDim,
                      fontWeight: isActive ? font.weightMedium : font.weightRegular,
                    }}
                  >
                    {lens.name}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Divider */}
          <div style={styles.divider} />

          {/* Step list */}
          <div style={styles.stepList}>
            {STEPS.map((step, idx) => {
              let icon: React.ReactNode;
              let labelStyle: React.CSSProperties = styles.stepLabel;

              if (isError && currentStep === step.key) {
                icon = <ErrorIcon />;
                labelStyle = { ...styles.stepLabel, color: color.error };
              } else if (idx < currentStepIdx || isComplete) {
                icon = <CheckIcon />;
                labelStyle = { ...styles.stepLabel, color: color.text };
              } else if (idx === currentStepIdx && !isComplete) {
                icon = <SpinnerIcon />;
                labelStyle = { ...styles.stepLabel, color: color.text, fontWeight: font.weightMedium };
              } else {
                icon = <PendingIcon />;
              }

              // Show elapsed time for completed steps
              const stepTime = status?.step_times?.[step.key];
              const timeLabel = stepTime ? `${stepTime}s` : '';

              return (
                <div key={step.key} style={styles.stepRow}>
                  {icon}
                  <span style={labelStyle}>{step.label}</span>
                  {timeLabel && <span style={styles.stepTime}>{timeLabel}</span>}
                </div>
              );
            })}
          </div>

          {/* Progress bar */}
          <div style={styles.progressContainer}>
            <div style={styles.progressTrack}>
              <div
                style={{
                  ...styles.progressFill,
                  width: `${progress}%`,
                  backgroundColor: isError ? color.error : color.lensPerformance,
                  transition: 'width 0.6s ease-out',
                }}
              />
            </div>
            <span style={styles.progressLabel}>{progress}%</span>
          </div>

          {/* Time estimate or redirect message */}
          {isComplete ? (
            <p style={styles.note}>
              ✓ Analysis complete — redirecting to results…
            </p>
          ) : isError ? (
            <div style={styles.errorBlock}>
              <p style={styles.errorMessage}>
                {status?.error_message || 'An error occurred during analysis.'}
              </p>
              <button
                onClick={handleRetry}
                disabled={retrying}
                style={styles.retryBtn}
              >
                {retrying ? 'Retrying…' : 'Retry Analysis'}
              </button>
            </div>
          ) : (
            <p style={styles.note}>
              Analysis typically takes 60–90 seconds
            </p>
          )}
        </div>

        {/* Connection error */}
        {error && !status && (
          <div style={styles.connectionError}>
            Unable to connect: {error}
          </div>
        )}
      </main>

      {/* CSS animation for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/* ── Styles ────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: color.bgPage,
  },
  main: {
    flex: 1,
    padding: `${space.xl} ${space.xxl}`,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  header: {
    width: '100%',
    maxWidth: 640,
    marginBottom: space.xl,
  },
  headerLabel: {
    fontFamily: font.family,
    fontSize: font.sizeXl,
    fontWeight: font.weightBold,
    color: color.text,
  },
  headerDivider: {
    margin: `0 ${space.sm}`,
    fontFamily: font.family,
    fontSize: font.sizeXl,
    fontWeight: font.weightRegular,
    color: color.border,
  },
  card: {
    width: '100%',
    maxWidth: 640,
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: color.shadowMd,
  },

  /* Lens icon row */
  lensRow: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: `${space.md} 0`,
  },
  lensItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: space.xs,
  },
  lensIcon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 52,
    height: 52,
    borderRadius: '50%',
    backgroundColor: color.bgPage,
  },
  lensLabel: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
    textAlign: 'center',
  },

  /* Divider */
  divider: {
    height: 1,
    backgroundColor: color.border,
    margin: `${space.lg} 0`,
  },

  /* Step list */
  stepList: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.md,
    marginBottom: space.xl,
  },
  stepRow: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
  },
  stepLabel: {
    fontFamily: font.family,
    fontSize: font.sizeBase,
    color: color.textDim,
    flex: 1,
  },
  stepTime: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    minWidth: 40,
    textAlign: 'right',
  },

  /* Progress bar */
  progressContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
    marginBottom: space.md,
  },
  progressTrack: {
    flex: 1,
    height: 8,
    backgroundColor: color.bgPage,
    borderRadius: radius.pill,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: radius.pill,
  },
  progressLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
    minWidth: 36,
    textAlign: 'right',
  },

  /* Notes & errors */
  note: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    textAlign: 'center',
    margin: 0,
    padding: `${space.sm} 0`,
  },
  errorBlock: {
    textAlign: 'center',
    padding: `${space.md} 0`,
  },
  errorMessage: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.error,
    margin: `0 0 ${space.md} 0`,
    padding: space.sm,
    backgroundColor: '#FEE2E2',
    borderRadius: radius.md,
  },
  retryBtn: {
    padding: `${space.sm} ${space.xl}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
  },
  connectionError: {
    marginTop: space.lg,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.error,
    textAlign: 'center',
  },
};
