import { cn } from "@/lib/utils"
import { ExternalLink, CheckCircle, Filter } from "lucide-react"
import { LoadingSkeleton } from "./LoadingSkeleton"
import { memo } from "react"

/**
 * Video routing decision types
 */
export type RoutingDecision = "routed" | "filtered"

/**
 * Video data for row display
 */
export interface VideoRowData {
  id: string
  title: string
  duration?: string
  routingDecision: RoutingDecision
  routingTarget?: string // Playlist name or filter reason
  videoUrl?: string
}

/**
 * Props for VideoRow component
 */
export interface VideoRowProps {
  /** Video data to display */
  video: VideoRowData
  /** Visual variant */
  variant?: RoutingDecision
  /** Click handler */
  onClick?: (video: VideoRowData) => void
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Loading skeleton for VideoRow
 */
function VideoRowSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-3 p-3 rounded-md", className)}>
      <LoadingSkeleton variant="rectangle" className="w-32 h-18 flex-shrink-0" />
      <div className="flex-1 min-w-0 space-y-2">
        <LoadingSkeleton variant="text" className="h-4 w-3/4" />
        <LoadingSkeleton variant="text" className="h-3 w-24" />
      </div>
    </div>
  )
}

/**
 * Format duration from seconds or MM:SS string
 */
function formatDuration(duration?: string): string {
  if (!duration) return ""
  // If already formatted, return as-is
  if (duration.includes(":")) return duration
  // Otherwise assume seconds
  const seconds = parseInt(duration, 10)
  if (isNaN(seconds)) return duration
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

/**
 * VideoRow displays a video with routing decision badge.
 * Shows routed (green) or filtered (gray) state with target/reason.
 * Memoized for performance optimization.
 * 
 * @example
 * ```tsx
 * <VideoRow
 *   video={{
 *     id: "1",
 *     title: "Amazing Video",
 *     duration: "10:30",
 *     routingDecision: "routed",
 *     routingTarget: "Tech Playlist",
 *     videoUrl: "https://youtube.com/watch?v=..."
 *   }}
 *   onClick={(video) => window.open(video.videoUrl, "_blank")}
 * />
 * ```
 */
const VideoRowComponent = memo(function VideoRow({
  video,
  variant,
  onClick,
  isLoading = false,
  className,
}: VideoRowProps) {
  if (isLoading) {
    return <VideoRowSkeleton className={className} />
  }

  const effectiveVariant = variant || video.routingDecision
  const isRouted = effectiveVariant === "routed"
  
  const handleClick = () => {
    if (video.videoUrl) {
      window.open(video.videoUrl, "_blank", "noopener,noreferrer")
    }
    onClick?.(video)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 rounded-md transition-all",
        "hover:bg-muted cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`Open ${video.title} in YouTube`}
    >
      {/* Thumbnail placeholder */}
      <div className="w-32 h-18 bg-muted rounded flex items-center justify-center flex-shrink-0" aria-hidden="true">
        <ExternalLink className="size-5 text-muted-foreground" />
      </div>

      {/* Video info */}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium truncate">{video.title}</h4>
        <div className="flex items-center gap-2 mt-1">
          {video.duration && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(video.duration)}
            </span>
          )}
          {/* Routing badge */}
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
              isRouted
                ? "bg-[var(--color-success)]/10 text-[var(--color-success)]"
                : "bg-muted text-muted-foreground"
            )}
          >
            {isRouted ? (
              <>
                <CheckCircle className="size-3" aria-hidden="true" />
                → {video.routingTarget || "Routed"}
              </>
            ) : (
              <>
                <Filter className="size-3" aria-hidden="true" />
                Filtered: {video.routingTarget || "Unknown"}
              </>
            )}
          </span>
        </div>
      </div>
    </div>
  )
})

export const VideoRow = Object.assign(VideoRowComponent, {
  Skeleton: VideoRowSkeleton,
})

export default VideoRow
