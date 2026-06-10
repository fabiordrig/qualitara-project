import { useMemo, useState } from "react"
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import type { AnomalyRecord, VehicleRow } from "./types"
import { ANOMALY_LABELS } from "./constants"
import { StatusBadge } from "./StatusBadge"

interface EnrichedRow extends VehicleRow {
  latest_anomaly_type?: string
}

interface VehicleTableProps {
  vehicles: VehicleRow[]
  anomalies: AnomalyRecord[]
  isLoading: boolean
  isError: boolean
}

const TH_STYLE: React.CSSProperties = {
  fontFamily: 'var(--font-label)',
  fontSize: '11px',
  fontWeight: 700,
  letterSpacing: '0.10em',
  textTransform: 'uppercase',
  color: 'var(--text-secondary)',
  padding: '0 14px',
  height: '36px',
  background: 'var(--bg-surface)',
  borderBottom: '1px solid var(--border-strong)',
  cursor: 'pointer',
  userSelect: 'none',
  whiteSpace: 'nowrap',
}

const TD_STYLE: React.CSSProperties = {
  padding: '0 14px',
  height: '36px',
  borderBottom: '1px solid var(--border-subtle)',
}

export function VehicleTable({ vehicles, anomalies, isLoading, isError }: VehicleTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const enrichedRows = useMemo<EnrichedRow[]>(() => {
    const latestByVehicle: Record<string, string> = {}
    for (const a of anomalies) {
      if (!(a.vehicle_id in latestByVehicle)) {
        latestByVehicle[a.vehicle_id] = a.anomaly_type
      }
    }
    return vehicles.map((v) => ({
      ...v,
      latest_anomaly_type: latestByVehicle[v.vehicle_id],
    }))
  }, [vehicles, anomalies])

  const columns = useMemo<ColumnDef<EnrichedRow>[]>(
    () => [
      {
        accessorKey: "vehicle_id",
        header: "Vehicle",
        cell: ({ getValue }) => (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-primary)' }}>
            {getValue<string>()}
          </span>
        ),
      },
      {
        accessorKey: "current_status",
        header: "Status",
        cell: ({ getValue }) => <StatusBadge status={getValue<string>()} />,
      },
      {
        accessorKey: "current_battery",
        header: "Battery %",
        cell: ({ getValue }) => {
          const val = getValue<number>()
          const isCritical = val < 15
          return (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              color: isCritical ? 'var(--status-fault)' : 'var(--text-primary)',
              fontWeight: isCritical ? 600 : 400,
              display: 'block',
              textAlign: 'right',
              ...(isCritical ? { animation: 'fault-pulse 2s ease-in-out infinite' } : {}),
            }}>
              {val.toFixed(1)}%
            </span>
          )
        },
      },
      {
        accessorKey: "latest_anomaly_type",
        header: "Latest Anomaly",
        cell: ({ getValue }) => {
          const raw = getValue<string | undefined>()
          if (!raw) {
            return <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>—</span>
          }
          const isFault = raw === 'fault_status'
          return (
            <span style={{
              fontFamily: 'var(--font-label)',
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.06em',
              color: isFault ? 'var(--status-fault)' : 'var(--text-secondary)',
            }}>
              {ANOMALY_LABELS[raw] ?? raw}
            </span>
          )
        },
      },
    ],
    []
  )

  const table = useReactTable<EnrichedRow>({
    data: enrichedRows,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: { sorting },
    onSortingChange: setSorting,
  })

  const errorBanner = isError ? (
    <div role="alert" style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      background: 'rgba(255,61,61,0.08)',
      borderLeft: '2px solid var(--status-fault)',
      color: 'var(--status-fault)',
      padding: '8px 14px',
      fontSize: '11px',
      fontFamily: 'var(--font-label)',
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
    }}>
      <span style={{ animation: 'fault-pulse 1.5s ease-in-out infinite' }}>⚠</span>
      Backend unreachable — retrying
    </div>
  ) : null

  const headerRow = (
    <thead>
      <tr>
        {['Vehicle', 'Status', 'Battery %', 'Latest Anomaly'].map((label, i) => (
          <th key={i} style={{
            ...TH_STYLE,
            textAlign: i === 2 ? 'right' : 'left',
          }}>
            {label}
          </th>
        ))}
      </tr>
    </thead>
  )

  // ── Loading skeleton ──
  if (isLoading && vehicles.length === 0) {
    return (
      <>
        {errorBanner}
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          {headerRow}
          <tbody>
            {Array.from({ length: 12 }).map((_, i) => (
              <tr key={i}>
                {[100, 72, 50, 90].map((w, ci) => (
                  <td key={ci} style={TD_STYLE}>
                    <div className="skeleton-bar" style={{ height: '12px', width: `${w}px` }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </>
    )
  }

  // ── Empty state ──
  if (!isLoading && vehicles.length === 0) {
    return (
      <>
        {errorBanner}
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          {headerRow}
          <tbody>
            <tr>
              <td colSpan={4} style={{
                ...TD_STYLE,
                textAlign: 'center',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-label)',
                fontSize: '12px',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                padding: '40px 14px',
              }}>
                No vehicles reporting — awaiting telemetry
              </td>
            </tr>
          </tbody>
        </table>
      </>
    )
  }

  // ── Populated ──
  return (
    <>
      {errorBanner}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {table.getHeaderGroups().flatMap((hg) =>
              hg.headers.map((header) => {
                const sorted = header.column.getIsSorted()
                const ariaSort = sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : 'none'
                const isRight = header.id === 'current_battery'
                return (
                  <th
                    key={header.id}
                    scope="col"
                    aria-sort={ariaSort}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{ ...TH_STYLE, textAlign: isRight ? 'right' : 'left' }}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {sorted && (
                        <span style={{ color: 'var(--text-accent)', fontSize: '9px' }}>
                          {sorted === 'asc' ? '▲' : '▼'}
                        </span>
                      )}
                    </span>
                  </th>
                )
              })
            )}
          </tr>
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row, idx) => {
            const isFaultRow = row.original.current_status === 'fault'
            return (
              <tr
                key={row.id}
                style={{
                  background: isFaultRow
                    ? 'var(--bg-fault-row)'
                    : idx % 2 === 0 ? 'var(--bg-base)' : 'var(--bg-surface)',
                  borderLeft: isFaultRow ? '2px solid var(--status-fault)' : '2px solid transparent',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background = 'var(--bg-hover)'
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background = isFaultRow
                    ? 'var(--bg-fault-row)'
                    : idx % 2 === 0 ? 'var(--bg-base)' : 'var(--bg-surface)'
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} style={TD_STYLE}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </>
  )
}
