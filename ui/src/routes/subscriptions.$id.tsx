import { createFileRoute } from '@tanstack/react-router'
import { useMemo } from 'react'
import { useSubscriptions, useSubscriptionStats, useRuns, useRunDecisions } from '@/hooks/use-api'
import { StatusCard } from '@/components/StatusCard'
import { VideoRow, type VideoRowData } from '@/components/VideoRow'
import { isApiError } from '@/lib/api-client'
import { Video, Filter, CheckCircle, Clock } from 'lucide-react'

export const Route = createFileRoute('/subscriptions/$id')({
  component: SubscriptionDetail,
})

function SubscriptionDetail() {
  const { id } = Route.useParams()
  
  const { data: subscriptions, isLoading: subsLoading, error: subsError } = useSubscriptions()
  const { isLoading: statsLoading } = useSubscriptionStats()
  // Get the most recent run ID first
  const { data: runs, isLoading: runsLoading } = useRuns({ limit: 1 })
  const latestRunId = runs?.[0]?.id
  // Get decisions from the most recent run (limit 500)
  // The hook will automatically disable if latestRunId is empty
  const { data: decisions, isLoading: decisionsLoading } = useRunDecisions(
    latestRunId || '',
    { limit: 500 }
  )
  
  const isLoading = subsLoading || statsLoading || runsLoading || decisionsLoading
  
  // Find the current subscription
  const subscription = subscriptions?.find((sub) => sub.subscription_id === id)
  
  // Filter decisions for this subscription
  const subscriptionDecisions = useMemo(() => {
    if (!decisions || !subscription) return []
    // Filter by channel_id since we don't have subscription_id in decisions
    return decisions.filter((d) => d.pipeline_id === subscription.channel_id)
  }, [decisions, subscription])
  
  // Calculate stats
  const totalVideos = subscriptionDecisions.length
  const routedCount = subscriptionDecisions.filter((d) => d.action === 'inserted').length
  const filteredCount = subscriptionDecisions.filter((d) => d.action === 'skipped').length
  
  // Map decisions to VideoRowData
  const videoRows: VideoRowData[] = subscriptionDecisions.map((decision) => ({
    id: decision.video_id,
    title: `Video ${decision.video_id}`, // API doesn't provide title yet
    duration: undefined, // API doesn't provide duration
    routingDecision: decision.action === 'inserted' ? 'routed' : 'filtered',
    routingTarget: decision.action === 'inserted' 
      ? 'Playlist' // API doesn't provide playlist name yet
      : decision.reason || decision.filter_name || 'Unknown',
    videoUrl: `https://youtube.com/watch?v=${decision.video_id}`,
  }))
  
  return (
    <div className="p-8">
      {/* Error state */}
      {subsError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive mb-6">
          <p className="font-medium">Failed to load subscription</p>
          <p className="text-sm mt-1">
            {isApiError(subsError) ? subsError.message : 'An unexpected error occurred'}
          </p>
        </div>
      )}
      
      {/* Loading state */}
      {isLoading && (
        <div className="space-y-6">
          <div className="h-8 w-64 bg-muted rounded animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatusCard.Skeleton key={i} />
            ))}
          </div>
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <VideoRow.Skeleton key={i} />
            ))}
          </div>
        </div>
      )}
      
      {/* Content */}
      {!isLoading && subscription && (
        <div className="space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold">{subscription.channel_title}</h1>
            <p className="text-muted-foreground mt-2">
              Channel ID: {subscription.channel_id}
            </p>
          </div>
          
          {/* Stats cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatusCard
              variant="neutral"
              icon={Video}
              label="Total Videos"
              value={totalVideos}
              timestamp="In cache"
            />
            <StatusCard
              variant="neutral"
              icon={Clock}
              label="Last Fetched"
              value="N/A"
              timestamp="Not available yet"
            />
            <StatusCard
              variant="success"
              icon={CheckCircle}
              label="Videos Routed"
              value={routedCount}
              timestamp={`${totalVideos > 0 ? Math.round((routedCount / totalVideos) * 100) : 0}% of total`}
            />
            <StatusCard
              variant="warning"
              icon={Filter}
              label="Videos Filtered"
              value={filteredCount}
              timestamp={`${totalVideos > 0 ? Math.round((filteredCount / totalVideos) * 100) : 0}% of total`}
            />
          </div>
          
          {/* Video list */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Video Routing History</h2>
            {videoRows.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <p>No video routing history available</p>
              </div>
            ) : (
              <div className="space-y-2">
                {videoRows.map((video) => (
                  <VideoRow key={video.id} video={video} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Not found state */}
      {!isLoading && !subscription && !subsError && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Subscription not found</p>
        </div>
      )}
    </div>
  )
}
