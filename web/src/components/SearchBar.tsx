import { color, font, space, radius } from '../tokens';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchBar({ value, onChange, placeholder = 'Enter project title' }: SearchBarProps) {
  return (
    <div style={styles.wrapper}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={styles.input}
      />
      <SearchIcon />
    </div>
  );
}

function SearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke={color.textDim}
      strokeWidth="2"
      style={styles.icon}
    >
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    position: 'relative',
    maxWidth: 360,
    width: '100%',
  },
  input: {
    width: '100%',
    padding: `${space.sm} ${space.md}`,
    paddingRight: '2.5rem',
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    fontFamily: font.family,
    fontSize: font.sizeBase,
    color: color.text,
    backgroundColor: color.bgCard,
    outline: 'none',
    boxSizing: 'border-box',
  },
  icon: {
    position: 'absolute',
    right: 12,
    top: '50%',
    transform: 'translateY(-50%)',
    pointerEvents: 'none',
  },
};
