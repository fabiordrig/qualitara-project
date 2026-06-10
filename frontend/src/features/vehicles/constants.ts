/**
 * D-08 status color map — dark-mode SCADA palette.
 * Semantic intent preserved (fault=red, moving=green, charging=blue, idle=gray).
 */
export const STATUS_STYLES: Record<string, { bg: string; text: string }> = Object.freeze({
  fault:    { bg: 'var(--status-fault-bg)',    text: 'var(--status-fault)'    },
  moving:   { bg: 'var(--status-moving-bg)',   text: 'var(--status-moving)'   },
  charging: { bg: 'var(--status-charging-bg)', text: 'var(--status-charging)' },
  idle:     { bg: 'var(--status-idle-bg)',      text: 'var(--status-idle)'     },
})

export const ANOMALY_LABELS: Record<string, string> = Object.freeze({
  fault_status:  'Fault',
  low_battery:   'Low Battery',
  speed_anomaly: 'Speed Anomaly',
  error_codes:   'Error Codes',
})

export const STATUS_ORDER = ['idle', 'moving', 'charging', 'fault'] as const
