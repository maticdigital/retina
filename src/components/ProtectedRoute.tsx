import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { color, font } from '../tokens';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={styles.loading}>
        <span style={styles.text}>Loading…</span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

const styles: Record<string, React.CSSProperties> = {
  loading: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: color.bgPage,
  },
  text: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.textMuted,
  },
};
