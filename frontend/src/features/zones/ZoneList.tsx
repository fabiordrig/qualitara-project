import { useMemo } from 'react'
import type { ZoneCount } from './types'

interface ZoneListProps {
  zones: ZoneCount[]
  isLoading: boolean
  isError: boolean
}

export function ZoneList({ zones, isLoading, isError }: ZoneListProps) {
  const sortedZones = useMemo(
    () => [...zones].sort((a, b) => b.entry_count - a.entry_count),
    [zones]
  )

  const maxCount = sortedZones[0]?.entry_count ?? 1

  return (
    <div style={{
      background: 'var(--bg-surface)',
      height: '100%',
      minHeight: 'calc(100vh - 48px)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Section header */}
      <div style={{
        height: '36px',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '16px',
        paddingRight: '16px',
        borderBottom: '1px solid var(--border-strong)',
        background: 'var(--bg-surface)',
        flexShrink: 0,
      }}>
        <span style={{
          fontFamily: 'var(--font-label)',
          fontSize: '11px',
          fontWeight: 700,
          letterSpacing: '0.10em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
        }}>
          Zone Entry Counts
        </span>
      </div>

      {/* Error */}
      {isError && (
        <div role="alert" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255,61,61,0.08)',
          borderLeft: '2px solid var(--status-fault)',
          color: 'var(--status-fault)',
          padding: '8px 16px',
          fontSize: '11px',
          fontFamily: 'var(--font-label)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          flexShrink: 0,
        }}>
          ⚠ Backend unreachable
        </div>
      )}

      {/* Skeleton */}
      {isLoading && zones.length === 0 && (
        <div style={{ padding: '8px 0' }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '9px 16px',
              gap: '12px',
            }}>
              <div className="skeleton-bar" style={{ height: '10px', width: `${50 + Math.random() * 30}%` }} />
              <div className="skeleton-bar" style={{ height: '10px', width: '24px' }} />
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && zones.length === 0 && (
        <div style={{
          padding: '40px 16px',
          textAlign: 'center',
          fontFamily: 'var(--font-label)',
          fontSize: '11px',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
        }}>
          No zone entries recorded
        </div>
      )}

      {/* Zone rows */}
      {sortedZones.length > 0 && (
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {sortedZones.map((zone, idx) => {
            const barPct = maxCount > 0 ? (zone.entry_count / maxCount) * 100 : 0
            const isActive = zone.entry_count > 0
            return (
              <div
                key={zone.zone_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 16px',
                  height: '34px',
                  borderBottom: '1px solid var(--border-subtle)',
                  background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.012)',
                  gap: '10px',
                }}
              >
                {/* Zone name */}
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  flex: '0 0 auto',
                  minWidth: '120px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {zone.zone_id}
                </span>

                {/* Bar track */}
                <div style={{
                  flex: 1,
                  height: '4px',
                  background: 'var(--border-subtle)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: `${barPct}%`,
                    background: isActive
                      ? `linear-gradient(90deg, var(--text-accent), rgba(240,164,22,0.6))`
                      : 'transparent',
                    borderRadius: '2px',
                    transition: 'width 0.4s ease',
                  }} />
                </div>

                {/* Count */}
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'var(--text-accent)' : 'var(--text-dim)',
                  flex: '0 0 auto',
                  minWidth: '20px',
                  textAlign: 'right',
                }}>
                  {zone.entry_count}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
