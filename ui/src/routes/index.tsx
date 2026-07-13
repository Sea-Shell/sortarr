import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { StatusCard } from '@/components/StatusCard'
import { ActivityFeed, type Activity } from '@/components/ActivityFeed'
import { RunTimeline, type RunItem } from '@/components/RunTimeline'
import { SearchBar } from '@/components/SearchBar'
import { PaginationControls } from '@/components/PaginationControls'
import { useHealth, useStats, useRuns, useRunDecisions } from '@/hooks/use-api'
import { formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function Dashboard() {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  // Fetch data (30s polling configured globally in query-client.ts)
  const { 
    data: health, 
    isLoading: healthLoading, 
    error: healthError,
    refetch: refetchHealth 
  } = useHealth()
  
  const { 
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats 
  } = useStats()
  
  const { 
    data: runs, 
    isLoading: runsLoading,
    error: runsError,
    refetch: refetchRuns 
  } = useRuns({ limit: 5 })

  // Get latest run ID for activity feed
  const latestRunId = runs?.[0]?.id
  const { 
    data: decisions,
    isLoading: decisionsLoading 
  } = useRunDecisions(
    latestRunId || '', 
    { limit: 10 }
  )

  // Determine overall loading state
  const isLoading = healthLoading || statsLoading || runsLoading
  const hasError = healthError || statsError || runsError

  // Map API data to component props
  const statusCards = {
    lastRun: {
      variant: runs?.[0]?.status === 'completed' ? 'success' as const : 
               runs?.[0]?.status === 'failed' ? 'error' as const : 
               'neutral' as const,
      label: 'Last Run',
      value: runs?.[0] ? formatRelativeTime(runs[0].completed_at || runs[0].started_at) : 'Never',
      timestamp: runs?.[0]?.status === 'completed' ? 'Completed successfully' :
                 runs?.[0]?.status === 'failed' ? runs[0].error_message || 'Failed' :
                 runs?.[0]?.status === 'running' ? 'In progress...' :
                 'No runs yet'
    },
    videosRouted: {
      variant: 'neutral' as const,
      label: 'Videos Routed',
      value: runs?.length ? runs.reduce((sum, run) => sum + run.videos_inserted, 0).toString() : '0',
      timestamp: 'All time'
    },
    activeSubs: {
      variant: 'neutral' as const,
      label: 'Active Subscriptions',
      value: health?.subscriptions_count?.toString() || '0',
      timestamp: 'Monitored'
    },
    quota: {
      variant: 'neutral' as const,
      label: 'Quota Used',
      value: health ? `${Math.round((health.quota_used_today / 10000) * 100)}%` : '0%',
      timestamp: `${health?.quota_remaining || 0} remaining today`
    }
  }

  // Map decisions to activities
  const activities: Activity[] = decisions
    ?.filter(d => d.action === 'inserted')
    .map(d => ({
      id: d.video_id,
      title: d.video_id,
      channel: d.pipeline_id,
      timestamp: 'Recently',
      playlist: d.filter_name || undefined
    })) || []

  // Map runs to timeline items
  const runItems: RunItem[] = runs?.map(run => ({
    id: run.id,
    status: run.status === 'completed' ? 'completed' as const :
            run.status === 'failed' ? 'failed' as const :
            'completed' as const,
    timestamp: formatRelativeTime(run.completed_at || run.started_at),
    videoCount: run.videos_inserted
  })) || []

  // Error state
  if (hasError) {
    return (
      <div className="p-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Monitor your Sortarr pipelines and activity
          </p>
        </div>
        
        <div className="flex items-center gap-4 p-4 border border-destructive rounded-lg bg-destructive/10">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <div className="flex-1">
            <p className="font-semibold">Failed to load dashboard data</p>
            <p className="text-sm text-muted-foreground">
              {healthError?.message || statsError?.message || runsError?.message}
            </p>
          </div>
          <Button 
            onClick={() => {
              refetchHealth()
              refetchStats()
              refetchRuns()
            }}
            variant="outline"
          >
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Monitor your Sortarr pipelines and activity
        </p>
      </div>

      {/* Authentication Warning */}
      {health && !health.authenticated && (
        <div className="flex items-center gap-4 p-4 border border-yellow-500 rounded-lg bg-yellow-500/10">
          <AlertCircle className="h-5 w-5 text-yellow-500" />
          <div className="flex-1">
            <p className="font-semibold">Not Authenticated</p>
            <p className="text-sm text-muted-foreground">
              YouTube API is not authenticated. Some features may be unavailable.
            </p>
          </div>
        </div>
      )}

      {/* Status Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="status-cards">
        <StatusCard
          variant={statusCards.lastRun.variant}
          label={statusCards.lastRun.label}
          value={statusCards.lastRun.value}
          timestamp={statusCards.lastRun.timestamp}
          isLoading={isLoading}
          data-testid="status-card"
        />
        <StatusCard
          variant={statusCards.videosRouted.variant}
          label={statusCards.videosRouted.label}
          value={statusCards.videosRouted.value}
          timestamp={statusCards.videosRouted.timestamp}
          isLoading={isLoading}
          data-testid="status-card"
        />
        <StatusCard
          variant={statusCards.activeSubs.variant}
          label={statusCards.activeSubs.label}
          value={statusCards.activeSubs.value}
          timestamp={statusCards.activeSubs.timestamp}
          isLoading={isLoading}
          data-testid="status-card"
        />
        <StatusCard
          variant={statusCards.quota.variant}
          label={statusCards.quota.label}
          value={statusCards.quota.value}
          timestamp={statusCards.quota.timestamp}
          isLoading={isLoading}
          data-testid="status-card"
        />
      </div>

      {/* Search Bar */}
      <SearchBar
        value={searchTerm}
        onChange={setSearchTerm}
        placeholder="Search videos..."
        className="max-w-md"
      />

      {/* Activity Feed and Run Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div data-testid="activity-feed">
          <ActivityFeed
            activities={activities}
            compact
            isLoading={isLoading || decisionsLoading}
          />
        </div>
        <div data-testid="run-timeline">
          <RunTimeline
            runs={runItems}
            compact
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Pagination Controls */}
      <PaginationControls
        currentPage={currentPage}
        totalPages={5}
        onPageChange={setCurrentPage}
      />
    </div>
  )
}
