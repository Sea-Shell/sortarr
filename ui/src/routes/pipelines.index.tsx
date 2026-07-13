import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { usePipelines, useUpdatePipeline, useDeletePipeline } from '../hooks/use-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import LoadingSkeleton from '../components/LoadingSkeleton';
import type { Pipeline } from '../lib/types';

export const Route = createFileRoute('/pipelines/')({
  component: PipelinesList,
});

function PipelinesList() {
  const { data: pipelines, isLoading, error } = usePipelines();
  const updatePipeline = useUpdatePipeline();
  const deletePipeline = useDeletePipeline();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [pipelineToDelete, setPipelineToDelete] = useState<string | null>(null);

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      await updatePipeline.mutateAsync({ id, data: { enabled } });
    } catch (err) {
      console.error('Failed to toggle pipeline:', err);
    }
  };

  const handleDeleteClick = (id: string) => {
    setPipelineToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!pipelineToDelete) return;
    
    try {
      await deletePipeline.mutateAsync(pipelineToDelete);
      setDeleteDialogOpen(false);
      setPipelineToDelete(null);
    } catch (err) {
      console.error('Failed to delete pipeline:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold">Pipelines</h1>
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Pipelines</h1>
        <div className="text-red-500">Error loading pipelines: {error.message}</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Pipelines</h1>
          <p className="text-muted-foreground mt-1">
            Manage your content routing pipelines
          </p>
        </div>
        <Link to="/pipelines/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Pipeline
          </Button>
        </Link>
      </div>

      {!pipelines || pipelines.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              No pipelines yet. Create your first pipeline to start routing content.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {pipelines.map((pipeline) => (
            <PipelineCard
              key={pipeline.id}
              pipeline={pipeline}
              onToggle={handleToggleEnabled}
              onDelete={handleDeleteClick}
              isUpdating={updatePipeline.isPending}
              isDeleting={deletePipeline.isPending}
            />
          ))}
        </div>
      )}

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Pipeline</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this pipeline? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deletePipeline.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deletePipeline.isPending}
            >
              {deletePipeline.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface PipelineCardProps {
  pipeline: Pipeline;
  onToggle: (id: string, enabled: boolean) => void;
  onDelete: (id: string) => void;
  isUpdating: boolean;
  isDeleting: boolean;
}

function PipelineCard({ pipeline, onToggle, onDelete, isUpdating, isDeleting }: PipelineCardProps) {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate({ to: '/pipelines/$id', params: { id: pipeline.id } });
  };

  return (
    <Card 
      className="hover:shadow-lg transition-shadow cursor-pointer" 
      onClick={handleCardClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle>
              {pipeline.name}
            </CardTitle>
            <CardDescription className="mt-1">
              {pipeline.playlist_id ? 'Destination configured' : 'No destination set'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={pipeline.enabled}
              onCheckedChange={(checked) => onToggle(pipeline.id, checked)}
              disabled={isUpdating}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Subscription Scope:</span>
            <span className="font-medium">
              {pipeline.subscription_scope === 'all' ? 'All' : 'Selected'}
            </span>
          </div>
          {pipeline.duration_min_seconds !== null && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Min Duration:</span>
              <span className="font-medium">{pipeline.duration_min_seconds}s</span>
            </div>
          )}
          {pipeline.duration_max_seconds !== null && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Duration:</span>
              <span className="font-medium">{pipeline.duration_max_seconds}s</span>
            </div>
          )}
          <div className="flex justify-between pt-2 border-t">
            <span className="text-muted-foreground">Status:</span>
            <span className={`font-medium ${pipeline.enabled ? 'text-green-600' : 'text-gray-400'}`}>
              {pipeline.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(pipeline.id);
            }}
            disabled={isDeleting}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

