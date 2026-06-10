import { useEffect, useState } from 'react'
import { STATUS_STYLES, STATUS_ORDER } from '@/features/vehicles/constants'
import type { FleetStateItem } from '@/features/vehicles/types'

interface HeaderProps {
  fleetState: FleetStateItem[]
  dataUpdatedAt: number
}

export function Header({ fleetState, dataUpdatedAt }: HeaderProps) {
  const [secondsAgo, setSecondsAgo] = useState(0)

  useEffect(() => {
    setSecondsAgo(Math.floor((Date.now() - dataUpdatedAt) / 1000))
    const interval = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - dataUpdatedAt) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [dataUpdatedAt])

  const lastUpdatedLabel = secondsAgo < 2 ? 'LIVE' : `${secondsAgo}s`

  return (
    <header style={{
      height: '48px',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-strong)',
      borderLeft: '3px solid var(--text-accent)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingLeft: '20px',
      paddingRight: '20px',
      flexShrink: 0,
      gap: '24px',
    }}>
      {/* Title */}
      <span style={{
        fontFamily: 'var(--font-label)',
        fontSize: '18px',
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'var(--text-accent)',
        whiteSpace: 'nowrap',
      }}>
        Fleet Monitor
      </span>

      {/* Status pills */}
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flex: 1, justifyContent: 'center' }}>
        {STATUS_ORDER.map((status) => {
          const count = fleetState.find((f) => f.status === status)?.count ?? 0
          const styles = STATUS_STYLES[status]
          const isFault = status === 'fault' && count > 0
          return (
            <div
              key={status}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 10px',
                background: isFault ? 'var(--status-fault-bg)' : styles.bg,
                border: `1px solid ${isFault ? 'rgba(255,61,61,0.35)' : 'transparent'}`,
                borderRadius: '2px',
              }}
            >
              <span style={{
                width: '6px',
                height: '6px',
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
                opacity: count === 0 ? 0.45 : 1,
              }}>
                {status}
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                fontWeight: 600,
                color: styles.text,
                opacity: count === 0 ? 0.45 : 1,
                minWidth: '18px',
                textAlign: 'right',
              }}>
                {count}
              </span>
            </div>
          )
        })}
      </div>

      {/* Last updated */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        whiteSpace: 'nowrap',
      }}>
        <span className="live-dot" style={{
          background: secondsAgo < 5 ? 'var(--status-moving)' : 'var(--text-secondary)',
        }} />
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: secondsAgo < 5 ? 'var(--status-moving)' : 'var(--text-secondary)',
          letterSpacing: '0.04em',
        }}>
          {lastUpdatedLabel === 'LIVE' ? 'LIVE' : `↻ ${lastUpdatedLabel} ago`}
        </span>
      </div>
    </header>
  )
}
