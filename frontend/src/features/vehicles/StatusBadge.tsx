import { STATUS_STYLES } from "./constants"

export function StatusBadge({ status }: { status: string }) {
  const styles = STATUS_STYLES[status] ?? STATUS_STYLES.idle
  const isFault = status === 'fault'

  return (
    <span
      aria-label={status}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '2px 8px',
        background: styles.bg,
        borderRadius: '2px',
        border: isFault ? `1px solid rgba(255,61,61,0.30)` : '1px solid transparent',
      }}
    >
      <span style={{
        width: '5px',
        height: '5px',
        borderRadius: '50%',
        background: styles.text,
        flexShrink: 0,
        ...(isFault ? { animation: 'fault-pulse 1.5s ease-in-out infinite' } : {}),
      }} />
      <span style={{
        fontFamily: 'var(--font-label)',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: styles.text,
      }}>
        {status}
      </span>
    </span>
  )
}
