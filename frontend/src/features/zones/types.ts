/**
 * Wire-format types that exactly mirror the backend snake_case JSON.
 * DO NOT rename fields — these match the API response directly.
 */

export interface ZoneCount {
  zone_id: string
  entry_count: number
}
