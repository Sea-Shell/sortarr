import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useSubscriptions, useSubscriptionStats } from '@/hooks/use-api'
import { SubscriptionCard, type SubscriptionCardData } from '@/components/SubscriptionCard'
import { SearchBar } from '@/components/SearchBar'
import { isApiError } from '@/lib/api-client'

export const Route = createFileRoute('/subscriptions')({
  component: SubscriptionsList,
})

function SubscriptionsList() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  
  const { data: subscriptions, isLoading: subsLoading, error: subsError } = useSubscriptions()
  const { data: stats, isLoading: statsLoading } = useSubscriptionStats()
  
  const isLoading = subsLoading || statsLoading
  
  // Filter subscriptions by search term
  const filteredSubscriptions = subscriptions?.filter((sub) =>
    sub.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []
  
  // Map to SubscriptionCardData format
  const subscriptionCards: SubscriptionCardData[] = filteredSubscriptions.map((sub) => ({
    id: sub.id,
    title: sub.name,
    channelId: sub.pipeline_id,
    activityCount: stats?.by_pipeline[sub.pipeline_id] || 0,
    lastSeenAt: undefined, // API doesn't provide this yet
  }))
  
  const handleCardClick = (subscription: SubscriptionCardData) => {
    navigate({ to: `/subscriptions/${subscription.id}` })
  }
  
  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Subscriptions</h1>
        <p className="text-muted-foreground mt-2">
          {subscriptions?.length || 0} total subscriptions
        </p>
      </div>
      
      {/* Search bar */}
      <div className="mb-6">
        <SearchBar
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search subscriptions by name..."
          className="max-w-md"
        />
      </div>
      
      {/* Error state */}
      {subsError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
          <p className="font-medium">Failed to load subscriptions</p>
          <p className="text-sm mt-1">
            {isApiError(subsError) ? subsError.message : 'An unexpected error occurred'}
          </p>
        </div>
      )}
      
      {/* Loading state */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SubscriptionCard.Skeleton key={i} />
          ))}
        </div>
      )}
      
      {/* Subscriptions grid */}
      {!isLoading && !subsError && (
        <>
          {subscriptionCards.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              {searchTerm ? (
                <p>No subscriptions found matching "{searchTerm}"</p>
              ) : (
                <p>No subscriptions yet</p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {subscriptionCards.map((sub) => (
                <SubscriptionCard
                  key={sub.id}
                  subscription={sub}
                  onClick={handleCardClick}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
