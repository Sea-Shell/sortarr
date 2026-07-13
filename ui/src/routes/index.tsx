import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { StatusCard } from '@/components/StatusCard'
import { ActivityFeed, type Activity } from '@/components/ActivityFeed'
import { RunTimeline, type RunItem } from '@/components/RunTimeline'
import { SearchBar } from '@/components/SearchBar'
import { PaginationControls } from '@/components/PaginationControls'
import { SubscriptionCard, type SubscriptionCardData } from '@/components/SubscriptionCard'
import { VideoRow, type VideoRowData } from '@/components/VideoRow'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

// Mock data for testing
const mockActivities: Activity[] = [
  {
    id: '1',
    title: 'The Ultimate Guide to React Hooks',
    channel: 'Tech Channel',
    timestamp: '2 hours ago',
    playlist: 'React Tutorials',
  },
  {
    id: '2',
    title: 'Building Modern Web Apps with TypeScript',
    channel: 'Dev Academy',
    timestamp: '5 hours ago',
  },
  {
    id: '3',
    title: 'Advanced CSS Techniques',
    channel: 'Design Masters',
    timestamp: '1 day ago',
    playlist: 'CSS Deep Dive',
  },
]

const mockRuns: RunItem[] = [
  { id: '1', status: 'completed', timestamp: '2 hours ago', videoCount: 12 },
  { id: '2', status: 'completed', timestamp: '1 day ago', videoCount: 8 },
  { id: '3', status: 'failed', timestamp: '2 days ago', videoCount: 0 },
  { id: '4', status: 'completed', timestamp: '3 days ago', videoCount: 15 },
  { id: '5', status: 'completed', timestamp: '4 days ago', videoCount: 10 },
]

const mockSubscriptions: SubscriptionCardData[] = [
  {
    id: '1',
    title: 'Tech Channel',
    channelId: 'UC123',
    activityCount: 5,
    lastSeenAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
  },
  {
    id: '2',
    title: 'Dev Academy',
    channelId: 'UC456',
    activityCount: 0,
    lastSeenAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
  },
  {
    id: '3',
    title: 'Design Masters',
    channelId: 'UC789',
    activityCount: 3,
    lastSeenAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
  },
]

const mockVideos: VideoRowData[] = [
  {
    id: '1',
    title: 'The Ultimate Guide to React Hooks',
    duration: '15:30',
    routingDecision: 'routed',
    routingTarget: 'React Tutorials',
    videoUrl: 'https://youtube.com/watch?v=example1',
  },
  {
    id: '2',
    title: 'Building Modern Web Apps with TypeScript',
    duration: '22:45',
    routingDecision: 'filtered',
    routingTarget: 'Too long',
    videoUrl: 'https://youtube.com/watch?v=example2',
  },
  {
    id: '3',
    title: 'Advanced CSS Techniques',
    duration: '10:15',
    routingDecision: 'routed',
    routingTarget: 'CSS Deep Dive',
    videoUrl: 'https://youtube.com/watch?v=example3',
  },
]

function Dashboard() {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Monitor your Sortarr pipelines and activity
        </p>
      </div>

      {/* Status Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          variant="success"
          label="Last Run"
          value="2 hours ago"
          timestamp="Completed successfully"
          isLoading={isLoading}
        />
        <StatusCard
          variant="neutral"
          label="Videos Routed"
          value="142"
          timestamp="This month"
          isLoading={isLoading}
        />
        <StatusCard
          variant="neutral"
          label="Active Subscriptions"
          value="8"
          timestamp="Monitored"
          isLoading={isLoading}
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
        <ActivityFeed
          activities={mockActivities}
          compact
          isLoading={isLoading}
        />
        <RunTimeline
          runs={mockRuns}
          compact
          isLoading={isLoading}
        />
      </div>

      {/* Pagination Controls */}
      <PaginationControls
        currentPage={currentPage}
        totalPages={5}
        onPageChange={setCurrentPage}
      />

      {/* New Components Demo */}
      <div className="space-y-6 pt-6 border-t">
        <div>
          <h2 className="text-xl font-bold mb-4">New Components (Wave 5)</h2>
          
          {/* Subscription Cards */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Subscription Cards</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {mockSubscriptions.map((sub) => (
                <SubscriptionCard
                  key={sub.id}
                  subscription={sub}
                  onClick={(s) => console.log('Clicked subscription:', s.title)}
                  isLoading={isLoading}
                />
              ))}
            </div>
          </div>

          {/* Video Rows */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Video Rows</h3>
            <div className="space-y-2">
              {mockVideos.map((video) => (
                <VideoRow
                  key={video.id}
                  video={video}
                  isLoading={isLoading}
                />
              ))}
            </div>
          </div>

          {/* Loading Skeletons */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Loading Skeletons</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Text</p>
                <LoadingSkeleton variant="text" count={3} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Card</p>
                <LoadingSkeleton variant="card" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Circle</p>
                <LoadingSkeleton variant="circle" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Rectangle</p>
                <LoadingSkeleton variant="rectangle" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State Toggle (for testing) */}
      <div className="pt-4 border-t">
        <button
          onClick={() => setIsLoading(!isLoading)}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Toggle Loading State (Current: {isLoading ? 'Loading' : 'Loaded'})
        </button>
      </div>
    </div>
  )
}
