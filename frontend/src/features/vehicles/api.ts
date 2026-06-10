import type { VehicleRow, AnomalyRecord, FleetStateItem } from './types'
import { apiClient as api } from '@/lib/apiClient'

export async function fetchVehicles(): Promise<VehicleRow[]> {
  const response = await api.get<VehicleRow[]>('/vehicles')
  return response.data
}

export async function fetchAnomalies({ limit = 500 }: { limit?: number } = {}): Promise<AnomalyRecord[]> {
  const response = await api.get<AnomalyRecord[]>('/anomalies', { params: { limit } })
  return response.data
}

export async function fetchFleetState(): Promise<FleetStateItem[]> {
  const response = await api.get<FleetStateItem[]>('/fleet/state')
  return response.data
}
