import type { ZoneCount } from './types'
import { apiClient as api } from '@/lib/apiClient'

export async function fetchZoneCounts(): Promise<ZoneCount[]> {
  const response = await api.get<ZoneCount[]>('/zones/counts')
  return response.data
}
