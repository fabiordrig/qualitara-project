import { useDashboardData } from './hooks/useDashboardData'

function App() {
  const { vehicles } = useDashboardData()

  if (vehicles.isLoading) {
    return (
      <div style={{ padding: '24px', fontFamily: 'system-ui, sans-serif' }}>
        <p>Loading fleet data...</p>
      </div>
    )
  }

  if (vehicles.isError) {
    return (
      <div style={{ padding: '24px', fontFamily: 'system-ui, sans-serif' }}>
        <p style={{ color: '#DC2626' }}>
          Unable to reach backend. Retrying automatically.
        </p>
      </div>
    )
  }

  const vehicleCount = vehicles.data?.length ?? 0

  return (
    <div style={{ padding: '24px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '24px', marginBottom: '16px' }}>Fleet Telemetry Monitor</h1>
      <p>{vehicleCount} vehicles online</p>
    </div>
  )
}

export default App
