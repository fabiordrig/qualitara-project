import { Badge } from "@/components/ui/badge"
import { STATUS_STYLES } from "./constants"

/**
 * StatusBadge wraps the shadcn Badge primitive, applying the locked D-08
 * traffic-light colors (STATUS_STYLES) via inline styles.
 *
 * Accessibility: aria-label={status} ensures screen readers read the status
 * value, not just the color (UI-SPEC Accessibility Baseline).
 */
export function StatusBadge({ status }: { status: string }) {
  // Fall back to idle styling for unknown statuses — no crash.
  const styles = STATUS_STYLES[status] ?? STATUS_STYLES.idle

  return (
    <Badge
      variant="secondary"
      aria-label={status}
      style={{
        backgroundColor: styles.bg,
        color: styles.text,
      }}
    >
      {status}
    </Badge>
  )
}
