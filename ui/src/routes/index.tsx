import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { StatusCard } from '@/components/StatusCard'
import { ActivityFeed, type Activity } from '@/components/ActivityFeed'
import { RunTimeline, type RunItem } from '@/components/RunTimeline'
import { SearchBar } from '@/components/SearchBar'
import { PaginationControls } from '@/components/PaginationControls'

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
