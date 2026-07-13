import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Clock, CheckCircle2, AlertCircle, XCircle } from "lucide-react"
import { useNavigate } from "@tanstack/react-router"
import { memo, useCallback } from "react"

/**
 * Run status type
 */
export type RunStatus = "completed" | "running" | "failed"

/**
 * Run item for timeline
 */
export interface RunItem {
  id: string
  status: RunStatus
  timestamp: string
  videoCount: number
}

/**
 * Props for RunTimeline component
 */
export interface RunTimelineProps {
  /** Array of runs to display */
  runs: RunItem[]
  /** Compact mode shows fewer items */
  compact?: boolean
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Status dot configuration
 */
const statusConfig: Record<
  RunStatus,
  { color: string; icon: typeof CheckCircle2 }
> = {
  completed: {
    color: "bg-[var(--color-success)]",
    icon: CheckCircle2,
  },
  running: {
    color: "bg-[var(--color-warning)]",
    icon: AlertCircle,
  },
  failed: {
    color: "bg-[var(--color-error)]",
    icon: XCircle,
  },
}

/**
 * Loading skeleton for RunTimeline
 */
function RunTimelineSkeleton({ 
  compact = false, 
  className 
}: { 
  compact?: boolean
  className?: string 
}) {
  const itemCount = compact ? 5 : 20

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Run History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Array.from({ length: itemCount }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="size-3 rounded-full bg-muted animate-pulse" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                <div className="h-3 w-24 bg-muted rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * RunTimeline displays recent pipeline runs
 * Memoized for performance optimization
 * 
 * @example
 * ```tsx
 * <RunTimeline
 *   runs={recentRuns}
 *   compact
 * />
 * ```
 */
const RunTimelineComponent = memo(function RunTimeline({
  runs,
  compact = false,
  isLoading = false,
  className,
}: RunTimelineProps) {
  const navigate = useNavigate()

  const handleRunClick = useCallback((runId: string) => {
    navigate({ to: "/runs", search: { runId } })
  }, [navigate])

  if (isLoading) {
    return <RunTimelineSkeleton compact={compact} className={className} />
  }

  const displayedRuns = compact ? runs.slice(0, 5) : runs.slice(0, 20)

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Run History</CardTitle>
      </CardHeader>
      <CardContent>
        {displayedRuns.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Clock className="size-12 text-muted-foreground mb-3" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">No runs yet</p>
          </div>
        ) : (
          <div className="space-y-4" role="list" aria-label="Pipeline run history">
            {displayedRuns.map((run, index) => {
              const config = statusConfig[run.status]
              const Icon = config.icon

              return (
                <div
                  key={run.id}
                  role="listitem"
                  className="flex items-start gap-3 cursor-pointer hover:bg-muted/50 p-2 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  onClick={() => handleRunClick(run.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      handleRunClick(run.id)
                    }
                  }}
                  tabIndex={0}
                  aria-label={`${run.status} run from ${run.timestamp} with ${run.videoCount} videos`}
                >
                  {/* Status indicator with connecting line */}
                  <div className="flex flex-col items-center" aria-hidden="true">
                    <div className={cn("size-3 rounded-full", config.color)} />
                    {index < displayedRuns.length - 1 && (
                      <div className="w-px h-8 bg-border mt-1" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pt-[-2px]">
                    <div className="flex items-center gap-2">
                      <Icon className={cn("size-4", config.color.replace("bg-", "text-"))} aria-hidden="true" />
                      <span className="text-sm font-medium capitalize">
                        {run.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {run.timestamp}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {run.videoCount} {run.videoCount === 1 ? "video" : "videos"}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
})

export const RunTimeline = Object.assign(RunTimelineComponent, {
  Skeleton: RunTimelineSkeleton,
})

export default RunTimeline
