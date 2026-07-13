import { Card, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { CheckCircle2, AlertTriangle, XCircle, Info, type LucideIcon } from "lucide-react"

/**
 * Status card variant types
 */
export type StatusVariant = "success" | "warning" | "error" | "neutral"

/**
 * Props for StatusCard component
 */
export interface StatusCardProps {
  /** Visual variant of the card */
  variant: StatusVariant
  /** Icon to display (optional, defaults based on variant) */
  icon?: LucideIcon
  /** Label text */
  label: string
  /** Primary value to display */
  value: string | number
  /** Optional timestamp or secondary text */
  timestamp?: string
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Variant configuration for colors and default icons
 */
const variantConfig: Record<
  StatusVariant,
  { borderColor: string; bgColor: string; iconColor: string; icon: LucideIcon }
> = {
  success: {
    borderColor: "border-l-[var(--color-success)]",
    bgColor: "bg-[var(--color-success)]/10",
    iconColor: "text-[var(--color-success)]",
    icon: CheckCircle2,
  },
  warning: {
    borderColor: "border-l-[var(--color-warning)]",
    bgColor: "bg-[var(--color-warning)]/10",
    iconColor: "text-[var(--color-warning)]",
    icon: AlertTriangle,
  },
  error: {
    borderColor: "border-l-[var(--color-error)]",
    bgColor: "bg-[var(--color-error)]/10",
    iconColor: "text-[var(--color-error)]",
    icon: XCircle,
  },
  neutral: {
    borderColor: "border-l-[var(--color-primary)]",
    bgColor: "bg-[var(--color-primary)]/5",
    iconColor: "text-[var(--color-primary)]",
    icon: Info,
  },
}

/**
 * Loading skeleton for StatusCard
 */
function StatusCardSkeleton({ className }: { className?: string }) {
  return (
    <Card className={cn("border-l-4 border-l-border", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-full bg-muted animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-24 bg-muted rounded animate-pulse" />
            <div className="h-6 w-16 bg-muted rounded animate-pulse" />
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}

/**
 * StatusCard displays a metric with visual status indicator
 * 
 * @example
 * ```tsx
 * <StatusCard
 *   variant="success"
 *   label="Last Run"
 *   value="2 hours ago"
 *   timestamp="Completed successfully"
 * />
 * ```
 */
export function StatusCard({
  variant,
  icon: CustomIcon,
  label,
  value,
  timestamp,
  isLoading = false,
  className,
}: StatusCardProps) {
  if (isLoading) {
    return <StatusCardSkeleton className={className} />
  }

  const config = variantConfig[variant]
  const Icon = CustomIcon || config.icon

  return (
    <Card
      className={cn(
        "border-l-4 transition-all hover:shadow-md",
        config.borderColor,
        className
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          {/* Icon circle */}
          <div
            className={cn(
              "flex size-10 items-center justify-center rounded-full",
              config.bgColor
            )}
          >
            <Icon className={cn("size-5", config.iconColor)} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {label}
            </CardTitle>
            <div className="text-2xl font-bold mt-1 truncate">{value}</div>
            {timestamp && (
              <p className="text-xs text-muted-foreground mt-1 truncate">
                {timestamp}
              </p>
            )}
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}

StatusCard.Skeleton = StatusCardSkeleton

export default StatusCard
