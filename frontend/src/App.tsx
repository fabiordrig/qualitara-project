import { useDashboardData } from './hooks/useDashboardData'
import { Header } from './components/Header'
import { VehicleTable } from './features/vehicles/VehicleTable'
import { ZoneList } from './features/zones/ZoneList'

function App() {
  const { vehicles, anomalies, zones, fleetState } = useDashboardData()

  return (
    <div
      style={{
        minHeight: '100vh',
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
        display: 'flex',
        flexDirection: 'column',
        background: '#FFFFFF',
      }}
    >
      {/* Full-width header (D-02) */}
      <Header
        fleetState={fleetState.data ?? []}
        dataUpdatedAt={vehicles.dataUpdatedAt}
      />

      {/* Two-column body: 70% vehicles left, 30% zones right (D-01) */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          gap: '32px',
          padding: '24px',
          alignItems: 'flex-start',
        }}
      >
        {/* Left column: vehicle table ~70% */}
        <div style={{ flex: '0 0 70%' }}>
          <VehicleTable
            vehicles={vehicles.data ?? []}
            anomalies={anomalies.data ?? []}
            isLoading={vehicles.isLoading}
            isError={vehicles.isError || anomalies.isError}
          />
        </div>

        {/* Right column: zone list ~30% */}
        <div style={{ flex: '0 0 calc(30% - 32px)' }}>
          <ZoneList
            zones={zones.data ?? []}
            isLoading={zones.isLoading}
            isError={zones.isError}
          />
        </div>
      </div>
    </div>
  )
}

export default App
