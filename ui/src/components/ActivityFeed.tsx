import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Video, Clock } from "lucide-react"
import { memo } from "react"

/**
 * Activity item representing a video
 */
export interface Activity {
  id: string
  title: string
  channel: string
  timestamp: string
  playlist?: string
  thumbnailUrl?: string
}

/**
 * Props for ActivityFeed component
 */
export interface ActivityFeedProps {
  /** Array of activities to display */
  activities: Activity[]
  /** Compact mode shows fewer items */
  compact?: boolean
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Loading skeleton for ActivityFeed
 */
function ActivityFeedSkeleton({ 
  compact = false, 
  className 
}: { 
  compact?: boolean
  className?: string 
}) {
  const itemCount = compact ? 3 : 10

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Array.from({ length: itemCount }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <div className="size-16 rounded bg-muted animate-pulse shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 bg-muted rounded animate-pulse" />
                <div className="h-3 w-1/2 bg-muted rounded animate-pulse" />
                <div className="h-3 w-1/3 bg-muted rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * ActivityFeed displays recent video activity
 * Memoized for performance optimization
 * 
 * @example
 * ```tsx
 * <ActivityFeed
 *   activities={recentVideos}
 *   compact
 * />
 * ```
 */
const ActivityFeedComponent = memo(function ActivityFeed({
  activities,
  compact = false,
  isLoading = false,
  className,
}: ActivityFeedProps) {
  if (isLoading) {
    return <ActivityFeedSkeleton compact={compact} className={className} />
  }

  const displayedActivities = compact ? activities.slice(0, 3) : activities.slice(0, 10)

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {displayedActivities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Video className="size-12 text-muted-foreground mb-3" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3">
            {displayedActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                tabIndex={0}
                role="button"
                aria-label={`View ${activity.title} from ${activity.channel}`}
              >
                {/* Thumbnail */}
                <div className="size-16 rounded bg-muted shrink-0 flex items-center justify-center overflow-hidden" aria-hidden="true">
                  {activity.thumbnailUrl ? (
                    <img
                      src={activity.thumbnailUrl}
                      alt=""
                      className="size-full object-cover"
                    />
                  ) : (
                    <Video className="size-6 text-muted-foreground" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium truncate" title={activity.title}>
                    {activity.title}
                  </h4>
                  <p className="text-xs text-muted-foreground truncate mt-1">
                    {activity.channel}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="size-3 text-muted-foreground" aria-hidden="true" />
                    <span className="text-xs text-muted-foreground">
                      {activity.timestamp}
                    </span>
                    {activity.playlist && (
                      <>
                        <span className="text-xs text-muted-foreground" aria-hidden="true">•</span>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                          {activity.playlist}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
})

export const ActivityFeed = Object.assign(ActivityFeedComponent, {
  Skeleton: ActivityFeedSkeleton,
})

export default ActivityFeed
