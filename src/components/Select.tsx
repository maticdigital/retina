import { color, font, space, radius } from '../tokens';

interface SelectProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: { label: string; value: T }[];
}

export function Select<T extends string>({ value, onChange, options }: SelectProps<T>) {
  return (
    <div style={styles.wrapper}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        style={styles.select}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronIcon />
    </div>
  );
}

function ChevronIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke={color.textMuted}
      strokeWidth="2.5"
      style={styles.chevron}
    >
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    position: 'relative',
    display: 'inline-block',
  },
  select: {
    appearance: 'none',
    padding: `${space.sm} ${space.xl} ${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightMedium,
    color: color.text,
    backgroundColor: color.bgCard,
    cursor: 'pointer',
    outline: 'none',
    minWidth: 100,
  },
  chevron: {
    position: 'absolute',
    right: 10,
    top: '50%',
    transform: 'translateY(-50%)',
    pointerEvents: 'none',
  },
};
