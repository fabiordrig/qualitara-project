/**
 * Locked D-08 status color map and authoritative anomaly label map.
 * These values are locked — do not alter hex colors (D-08).
 *
 * Anomaly type contract (backend app/telemetry/service.py _anomaly_type):
 *   fault_status | low_battery | speed_anomaly | error_codes
 * Use low_battery (not the incorrect key from UI-SPEC).
 */

/** D-08 locked traffic-light status colors. Applied as inline styles on the shadcn Badge. */
export const STATUS_STYLES: Record<string, { bg: string; text: string }> = Object.freeze({
  fault:    { bg: '#FEE2E2', text: '#DC2626' },
  moving:   { bg: '#DCFCE7', text: '#16A34A' },
  charging: { bg: '#DBEAFE', text: '#2563EB' },
  idle:     { bg: '#F3F4F6', text: '#6B7280' },
})

/**
 * Human-readable labels for the authoritative backend anomaly_type values.
 * Source: backend/app/telemetry/service.py `_anomaly_type`
 * Unmapped values fall back to the raw string in consuming components.
 */
export const ANOMALY_LABELS: Record<string, string> = Object.freeze({
  fault_status:  'Fault',
  low_battery:   'Low Battery',
  speed_anomaly: 'Speed Anomaly',
  error_codes:   'Error Codes',
})

/** Status order for reuse (e.g., Header fleet-summary pills in 02-04). */
export const STATUS_ORDER = ['idle', 'moving', 'charging', 'fault'] as const
