import { useMemo, useState } from "react"
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { AnomalyRecord, VehicleRow } from "./types"
import { ANOMALY_LABELS } from "./constants"
import { StatusBadge } from "./StatusBadge"

/** VehicleRow enriched with the latest anomaly type merged from anomalies. */
interface EnrichedRow extends VehicleRow {
  latest_anomaly_type?: string
}

interface VehicleTableProps {
  vehicles: VehicleRow[]
  anomalies: AnomalyRecord[]
  isLoading: boolean
  isError: boolean
}

/**
 * VehicleTable — sortable 50-row vehicle table.
 *
 * - Markup via shadcn Table primitives (D-12)
 * - Sorting via TanStack Table useReactTable (D-13)
 * - D-08 status colors via StatusBadge
 * - Inline latest anomaly from anomalies (grouped by vehicle_id, first = most recent)
 * - Battery < 15 renders red and bold (ANOM-02)
 * - Loading / empty / error states per UI-SPEC
 */
export function VehicleTable({ vehicles, anomalies, isLoading, isError }: VehicleTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  // Memoised anomaly merge: group anomalies by vehicle_id, take first (API returns
  // timestamp desc, so first = most recent). Avoids re-deriving on every poll cycle.
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
          <span style={{ fontFamily: '"Courier New", monospace', color: "#111827" }}>
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
            <span
              style={{
                color: isCritical ? "#DC2626" : undefined,
                fontWeight: isCritical ? 700 : undefined,
                textAlign: "right",
                display: "block",
              }}
            >
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
            return <span style={{ color: "#D1D5DB" }}>—</span>
          }
          return (
            <span style={{ color: "#374151" }}>
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

  // ── Error banner (shown above table; stale data keeps rendering if present) ──
  const errorBanner = isError ? (
    <div
      role="alert"
      style={{
        backgroundColor: "#FEF2F2",
        color: "#DC2626",
        padding: "8px 16px",
        borderRadius: "4px",
        marginBottom: "8px",
        fontSize: "14px",
      }}
    >
      Unable to reach backend. Retrying automatically.
    </div>
  ) : null

  // ── Loading state: 10 skeleton rows ──
  if (isLoading && vehicles.length === 0) {
    return (
      <>
        {errorBanner}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Vehicle</TableHead>
              <TableHead scope="col">Status</TableHead>
              <TableHead scope="col">Battery %</TableHead>
              <TableHead scope="col">Latest Anomaly</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 10 }).map((_, i) => (
              <TableRow key={i} style={{ height: "40px" }}>
                {[120, 80, 60, 100].map((w, ci) => (
                  <TableCell key={ci}>
                    <div
                      style={{
                        height: "16px",
                        width: `${w}px`,
                        backgroundColor: "#E5E7EB",
                        borderRadius: "4px",
                        animation: "pulse 1.5s ease-in-out infinite",
                      }}
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </>
    )
  }

  // ── Empty state ──
  if (!isLoading && vehicles.length === 0) {
    return (
      <>
        {errorBanner}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Vehicle</TableHead>
              <TableHead scope="col">Status</TableHead>
              <TableHead scope="col">Battery %</TableHead>
              <TableHead scope="col">Latest Anomaly</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell
                colSpan={4}
                style={{ textAlign: "center", color: "#6B7280", padding: "24px" }}
              >
                No vehicles reporting. Waiting for telemetry data.
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </>
    )
  }

  // ── Populated state (also shown during error if stale data is available) ──
  return (
    <>
      {errorBanner}
      <Table>
        <TableHeader>
          <TableRow>
            {table.getHeaderGroups().map((headerGroup) =>
              headerGroup.headers.map((header) => {
                const isSorted = header.column.getIsSorted()
                const ariaSort =
                  isSorted === "asc"
                    ? "ascending"
                    : isSorted === "desc"
                    ? "descending"
                    : "none"
                return (
                  <TableHead
                    key={header.id}
                    scope="col"
                    aria-sort={ariaSort}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      cursor: "pointer",
                      userSelect: "none",
                      fontSize: "12px",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {isSorted === "asc" && (
                      <span style={{ color: "#2563EB", marginLeft: "4px" }}>▲</span>
                    )}
                    {isSorted === "desc" && (
                      <span style={{ color: "#2563EB", marginLeft: "4px" }}>▼</span>
                    )}
                  </TableHead>
                )
              })
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.id}
              style={{
                height: "40px",
                borderBottom: "1px solid #F3F4F6",
              }}
              className="hover:bg-[#F9FAFB]"
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}
