import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { STATUS_STYLES, STATUS_ORDER } from '@/features/vehicles/constants'
import type { FleetStateItem } from '@/features/vehicles/types'

interface HeaderProps {
  fleetState: FleetStateItem[]
  dataUpdatedAt: number
}

export function Header({ fleetState, dataUpdatedAt }: HeaderProps) {
  const [secondsAgo, setSecondsAgo] = useState(0)

  useEffect(() => {
    // Reset immediately on new data
    setSecondsAgo(Math.floor((Date.now() - dataUpdatedAt) / 1000))

    const interval = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - dataUpdatedAt) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [dataUpdatedAt])

  const lastUpdatedLabel = secondsAgo < 2 ? 'just now' : `${secondsAgo}s ago`

  return (
    <header
      style={{
        height: '56px',
        background: '#F9FAFB',
        borderBottom: '1px solid #E5E7EB',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingLeft: '24px',
        paddingRight: '24px',
        flexShrink: 0,
      }}
    >
      {/* Left: App title */}
      <span
        style={{
          fontSize: '20px',
          fontWeight: 600,
          lineHeight: 1.2,
          color: '#111827',
        }}
      >
        Fleet Monitor
      </span>

      {/* Center: Fleet status count pills (D-12: shadcn Badge, D-08: locked colors as inline styles) */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {STATUS_ORDER.map((status) => {
          const count = fleetState.find((f) => f.status === status)?.count ?? 0
          const styles = STATUS_STYLES[status]
          return (
            <Badge
              key={status}
              variant="secondary"
              style={{
                backgroundColor: styles.bg,
                color: styles.text,
                fontSize: '12px',
                fontWeight: 500,
              }}
            >
              {status}: {count}
            </Badge>
          )
        })}
      </div>

      {/* Right: Last updated indicator — timestamp only (D-09) */}
      <span
        style={{
          fontSize: '12px',
          lineHeight: 1.4,
          color: '#6B7280',
        }}
      >
        Last updated: {lastUpdatedLabel}
      </span>
    </header>
  )
}
