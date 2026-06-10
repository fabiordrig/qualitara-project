import { useDashboardData } from './hooks/useDashboardData'
import { Header } from './components/Header'
import { VehicleTable } from './features/vehicles/VehicleTable'
import { ZoneList } from './features/zones/ZoneList'

function App() {
  const { vehicles, anomalies, zones, fleetState } = useDashboardData()

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-base)',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'var(--font-ui)',
    }}>
      <Header
        fleetState={fleetState.data ?? []}
        dataUpdatedAt={vehicles.dataUpdatedAt}
      />

      <div style={{
        display: 'flex',
        flex: 1,
        gap: 0,
        alignItems: 'flex-start',
        overflow: 'hidden',
      }}>
        {/* Left column: vehicle table ~70% */}
        <div style={{
          flex: '0 0 70%',
          borderRight: '1px solid var(--border-subtle)',
          minHeight: 'calc(100vh - 48px)',
          overflowX: 'auto',
        }}>
          <VehicleTable
            vehicles={vehicles.data ?? []}
            anomalies={anomalies.data ?? []}
            isLoading={vehicles.isLoading}
            isError={vehicles.isError || anomalies.isError}
          />
        </div>

        {/* Right column: zone list ~30% */}
        <div style={{ flex: '0 0 30%', minHeight: 'calc(100vh - 48px)' }}>
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
