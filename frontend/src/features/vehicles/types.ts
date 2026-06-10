/**
 * Wire-format types that exactly mirror the backend snake_case JSON.
 * DO NOT rename fields — these match the API response directly.
 *
 * Anomaly type contract (backend app/telemetry/service.py _anomaly_type):
 *   fault_status | low_battery | speed_anomaly | error_codes
 * Do NOT use battery_critical — the correct low-battery value is low_battery.
 */

export interface VehicleRow {
  vehicle_id: string
  current_status: 'idle' | 'moving' | 'charging' | 'fault'
  current_battery: number
  latest_seen: string | null
  /** Client-enriched field — populated on the frontend, never from the API */
  latest_anomaly_type?: string
}

export interface AnomalyRecord {
  id: number
  vehicle_id: string
  timestamp: string
  anomaly_type: string
  raw_event_id: number | null
}

export interface FleetStateItem {
  status: string
  count: number
}

export type SortKey = 'vehicle_id' | 'current_status' | 'current_battery' | 'latest_anomaly_type'
export type SortDir = 'asc' | 'desc' | null
