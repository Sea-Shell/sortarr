import { type UseQueryOptions } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useRuns, useRunDecisions } from '@/hooks/use-api'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { VideoRow } from '@/components/VideoRow'
import { ChevronDown, ChevronRight, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Run, Decision } from '@/lib/types'
import type { ApiError } from '@/lib/api-client'

export const Route = createFileRoute('/runs')({
  component: RunHistory,
})

type StatusFilter = 'all' | 'success' | 'error' | 'quota-blocked'

function RunHistory() {
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  
  const { data: runs, isLoading, error } = useRuns()
  const { data: decisions, isLoading: decisionsLoading } = useRunDecisions(
    expandedRunId || '',
    undefined,
    {
      enabled: !!expandedRunId,
    } as UseQueryOptions<Decision[], ApiError>
  )

  // Filter runs by status
  const filteredRuns = runs?.filter(run => {
    if (statusFilter === 'all') return true
    if (statusFilter === 'success') return run.status === 'completed' && !run.error_message
    if (statusFilter === 'error') return run.status === 'failed' || run.error_message
    if (statusFilter === 'quota-blocked') return run.error_message?.toLowerCase().includes('quota')
    return true
  })

  const toggleExpand = (runId: string) => {
    setExpandedRunId(expandedRunId === runId ? null : runId)
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Run History</h1>
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          Failed to load runs: {error.message}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Run History</h1>
        
        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Filter:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="px-3 py-1.5 rounded-md border bg-background text-sm"
          >
            <option value="all">All Runs</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="quota-blocked">Quota Blocked</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <LoadingSkeleton key={i} variant="rectangle" className="h-24 w-full" />
          ))}
        </div>
      ) : !filteredRuns || filteredRuns.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {statusFilter === 'all' ? 'No runs yet' : `No ${statusFilter} runs found`}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRuns.map(run => (
            <RunRow
              key={run.id}
              run={run}
              isExpanded={expandedRunId === run.id}
              onToggle={() => toggleExpand(run.id)}
              decisions={expandedRunId === run.id ? decisions : undefined}
              decisionsLoading={expandedRunId === run.id && decisionsLoading}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface RunRowProps {
  run: Run
  isExpanded: boolean
  onToggle: () => void
  decisions?: Decision[]
  decisionsLoading?: boolean
}

function RunRow({ run, isExpanded, onToggle, decisions, decisionsLoading }: RunRowProps) {
  const hasError = run.status === 'failed' || !!run.error_message
  const isQuotaBlocked = run.error_message?.toLowerCase().includes('quota')

  const statusIcon = hasError ? (
    <XCircle className="size-5 text-destructive" />
  ) : isQuotaBlocked ? (
    <AlertCircle className="size-5 text-yellow-500" />
  ) : (
    <CheckCircle className="size-5 text-[var(--color-success)]" />
  )

  const statusText = hasError ? 'Failed' : isQuotaBlocked ? 'Quota Blocked' : 'Success'
  const statusColor = hasError ? 'text-destructive' : isQuotaBlocked ? 'text-yellow-500' : 'text-[var(--color-success)]'

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Run Summary */}
      <button
        onClick={onToggle}
        className="w-full p-4 hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-start gap-4">
          {/* Expand Icon */}
          <div className="mt-1">
            {isExpanded ? (
              <ChevronDown className="size-5 text-muted-foreground" />
            ) : (
              <ChevronRight className="size-5 text-muted-foreground" />
            )}
          </div>

          {/* Status Icon */}
          <div className="mt-0.5">{statusIcon}</div>

          {/* Run Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <span className={cn("font-medium", statusColor)}>{statusText}</span>
              <span className="text-sm text-muted-foreground">
                {run.trigger === 'manual' ? 'Manual' : 'Scheduled'}
              </span>
              {run.started_at && (
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock className="size-3" />
                  {new Date(run.started_at).toLocaleString()}
                </span>
              )}
            </div>

            {/* Stats */}
            <div className="flex items-center gap-4 text-sm">
              <span className="text-muted-foreground">
                Collected: <span className="font-medium text-foreground">{run.activities_collected}</span>
              </span>
              <span className="text-muted-foreground">
                Enriched: <span className="font-medium text-foreground">{run.videos_enriched}</span>
              </span>
              <span className="text-muted-foreground">
                Inserted: <span className="font-medium text-[var(--color-success)]">{run.videos_inserted}</span>
              </span>
              <span className="text-muted-foreground">
                Skipped: <span className="font-medium text-foreground">{run.videos_skipped}</span>
              </span>
              <span className="text-muted-foreground">
                Quota: <span className="font-medium text-foreground">{run.quota_used}</span>
              </span>
            </div>

            {/* Error Message */}
            {run.error_message && (
              <div className="mt-2 text-sm text-destructive">
                {run.error_message}
              </div>
            )}
          </div>
        </div>
      </button>

      {/* Expanded Decisions */}
      {isExpanded && (
        <div className="border-t bg-muted/20 p-4">
          <h3 className="font-medium mb-3">Routing Decisions</h3>
          {decisionsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <LoadingSkeleton key={i} variant="rectangle" className="h-16 w-full" />
              ))}
            </div>
          ) : !decisions || decisions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No decisions recorded</p>
          ) : (
            <div className="space-y-2">
              {decisions.map((decision, idx) => (
                <VideoRow
                  key={`${decision.video_id}-${idx}`}
                  video={{
                    id: decision.video_id,
                    title: decision.video_id,
                    routingDecision: decision.action === 'inserted' ? 'routed' : 'filtered',
                    routingTarget: decision.action === 'inserted' 
                      ? 'Playlist' 
                      : decision.reason || decision.filter_name || 'Unknown',
                    videoUrl: `https://youtube.com/watch?v=${decision.video_id}`,
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

