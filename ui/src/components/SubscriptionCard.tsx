import { Card, CardHeader } from "@/components/ui/card"
import { cn, formatRelativeTime } from "@/lib/utils"
import { User, Activity } from "lucide-react"
import { LoadingSkeleton } from "./LoadingSkeleton"

/**
 * Subscription data for card display
 */
export interface SubscriptionCardData {
  id: string
  title: string
  channelId: string
  activityCount: number
  lastSeenAt?: string
}

/**
 * Props for SubscriptionCard component
 */
export interface SubscriptionCardProps {
  /** Subscription data to display */
  subscription: SubscriptionCardData
  /** Click handler */
  onClick?: (subscription: SubscriptionCardData) => void
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Loading skeleton for SubscriptionCard
 */
function SubscriptionCardSkeleton({ className }: { className?: string }) {
  return (
    <Card className={cn("cursor-pointer", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <LoadingSkeleton variant="circle" className="size-10 flex-shrink-0" />
          <div className="flex-1 min-w-0 space-y-2">
            <LoadingSkeleton variant="text" className="h-4 w-32" />
            <LoadingSkeleton variant="text" className="h-3 w-24" />
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}

/**
 * SubscriptionCard displays a YouTube subscription with activity count
 * and last seen timestamp. Shows active/inactive visual state based on
 * recent activity.
 * 
 * @example
 * ```tsx
 * <SubscriptionCard
 *   subscription={{
 *     id: "1",
 *     title: "Tech Channel",
 *     channelId: "UC123",
 *     activityCount: 5,
 *     lastSeenAt: "2024-01-15T10:30:00Z"
 *   }}
 *   onClick={(sub) => navigate(`/subscriptions/${sub.id}`)}
 * />
 * ```
 */
export function SubscriptionCard({
  subscription,
  onClick,
  isLoading = false,
  className,
}: SubscriptionCardProps) {
  if (isLoading) {
    return <SubscriptionCardSkeleton className={className} />
  }

  const hasActivity = subscription.activityCount > 0
  const isActive = hasActivity && subscription.lastSeenAt
  
  const handleClick = () => {
    onClick?.(subscription)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      onClick?.(subscription)
    }
  }

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isActive ? "border-l-4 border-l-[var(--color-success)]" : "opacity-75",
        className
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`View ${subscription.title} subscription details`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex size-10 items-center justify-center rounded-full flex-shrink-0",
              isActive
                ? "bg-[var(--color-success)]/10"
                : "bg-muted"
            )}
          >
            <User
              className={cn(
                "size-5",
                isActive
                  ? "text-[var(--color-success)]"
                  : "text-muted-foreground"
              )}
            />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate">{subscription.title}</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
              {hasActivity && (
                <span className="flex items-center gap-1">
                  <Activity className="size-3" />
                  {subscription.activityCount}
                </span>
              )}
              <span>{formatRelativeTime(subscription.lastSeenAt)}</span>
            </div>
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}

SubscriptionCard.Skeleton = SubscriptionCardSkeleton

export default SubscriptionCard
