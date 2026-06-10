import { useQuery } from '@tanstack/react-query'
import { fetchVehicles, fetchAnomalies, fetchFleetState } from '../features/vehicles/api'
import { fetchZoneCounts } from '../features/zones/api'

const POLL_INTERVAL = 2500

export function useDashboardData() {
  const vehicles = useQuery({
    queryKey: ['vehicles'],
    queryFn: fetchVehicles,
    refetchInterval: POLL_INTERVAL,
    refetchIntervalInBackground: true,
  })

  const anomalies = useQuery({
    queryKey: ['anomalies'],
    queryFn: () => fetchAnomalies({ limit: 500 }),
    refetchInterval: POLL_INTERVAL,
    refetchIntervalInBackground: true,
  })

  const zones = useQuery({
    queryKey: ['zones'],
    queryFn: fetchZoneCounts,
    refetchInterval: POLL_INTERVAL,
    refetchIntervalInBackground: true,
  })

  const fleetState = useQuery({
    queryKey: ['fleetState'],
    queryFn: fetchFleetState,
    refetchInterval: POLL_INTERVAL,
    refetchIntervalInBackground: true,
  })

  return { vehicles, anomalies, zones, fleetState }
}
