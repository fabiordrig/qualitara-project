import { useMemo } from 'react'
import type { ZoneCount } from './types'

interface ZoneListProps {
  zones: ZoneCount[]
  isLoading: boolean
  isError: boolean
}

export function ZoneList({ zones, isLoading, isError }: ZoneListProps) {
  // Sort by entry_count descending — busiest first (D-07)
  const sortedZones = useMemo(
    () => [...zones].sort((a, b) => b.entry_count - a.entry_count),
    [zones]
  )

  return (
    <div
      style={{
        background: '#F9FAFB',
        padding: '24px',
        overflowY: 'auto',
        maxHeight: 'calc(100vh - 56px)',
      }}
    >
      {/* Section heading */}
      <h2
        style={{
          fontSize: '16px',
          fontWeight: 600,
          lineHeight: 1.3,
          color: '#111827',
          margin: 0,
          marginBottom: '12px',
        }}
      >
        Zone Entry Counts
      </h2>

      {/* Error state */}
      {isError && (
        <div
          role="alert"
          style={{
            background: '#FEE2E2',
            color: '#DC2626',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px',
            marginBottom: '12px',
          }}
        >
          Unable to reach backend. Retrying automatically.
        </div>
      )}

      {/* Loading state: 5 skeleton rows */}
      {isLoading && zones.length === 0 && (
        <div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              style={{
                height: '36px',
                borderBottom: '1px solid #F3F4F6',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <div
                style={{
                  height: '16px',
                  width: '60%',
                  background: '#E5E7EB',
                  borderRadius: '4px',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
              <div
                style={{
                  height: '16px',
                  width: '20%',
                  background: '#E5E7EB',
                  borderRadius: '4px',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && zones.length === 0 && (
        <p
          style={{
            fontSize: '14px',
            color: '#6B7280',
            textAlign: 'center',
            marginTop: '24px',
          }}
        >
          No zone entries recorded yet.
        </p>
      )}

      {/* Populated: all zones sorted by count desc */}
      {sortedZones.length > 0 && (
        <div>
          {sortedZones.map((zone) => (
            <div
              key={zone.zone_id}
              style={{
                height: '36px',
                borderBottom: '1px solid #F3F4F6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {zone.zone_id}
              </span>
              <span
                style={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#111827',
                }}
              >
                {zone.entry_count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
