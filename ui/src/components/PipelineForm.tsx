import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  useCreatePipeline,
  useUpdatePipeline,
  usePlaylists,
  useMockPreview,
} from '../hooks/use-api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { useState } from 'react';
import { Eye } from 'lucide-react';
import type { Pipeline } from '../lib/types';

const pipelineSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  playlist_id: z.string().min(1, 'Playlist is required'),
  subscription_scope: z.enum(['all', 'selected']),
  duration_min_seconds: z.number().nullable(),
  duration_max_seconds: z.number().nullable(),
  selector_mode: z.enum(['AND', 'OR']),
  subscription_ids: z.array(z.string()),
  blocked_words: z.string(),
}).refine(
  (data) => {
    if (data.duration_min_seconds !== null && data.duration_max_seconds !== null) {
      return data.duration_min_seconds < data.duration_max_seconds;
    }
    return true;
  },
  {
    message: 'Minimum duration must be less than maximum duration',
    path: ['duration_max_seconds'],
  }
);

type PipelineFormData = z.infer<typeof pipelineSchema>;

interface PipelineFormProps {
  pipeline?: Pipeline;
  onSuccess: (id?: string) => void;
  onCancel: () => void;
}

export default function PipelineForm({ pipeline, onSuccess, onCancel }: PipelineFormProps) {
  const isEdit = !!pipeline;
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewData, setPreviewData] = useState<{ action: string; reason: string; filter_name: string } | null>(null);

  const { data: playlists } = usePlaylists();
  const createPipeline = useCreatePipeline();
  const updatePipeline = useUpdatePipeline();
  const mockPreview = useMockPreview();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<PipelineFormData>({
    resolver: zodResolver(pipelineSchema),
    defaultValues: {
      name: pipeline?.name || '',
      playlist_id: pipeline?.playlist_id || '',
      subscription_scope: (pipeline?.subscription_scope as 'all' | 'selected') || 'all',
      duration_min_seconds: pipeline?.duration_min_seconds || null,
      duration_max_seconds: pipeline?.duration_max_seconds || null,
      selector_mode: (pipeline?.selector_mode as 'AND' | 'OR') || 'AND',
      subscription_ids: pipeline?.subscription_ids || [],
      blocked_words: '',
    },
  });

  const subscriptionScope = watch('subscription_scope');

  const onSubmit = async (data: PipelineFormData) => {
    try {
      if (isEdit && pipeline) {
        await updatePipeline.mutateAsync({
          id: pipeline.id,
          data: {
            name: data.name,
            playlist_id: data.playlist_id,
            subscription_scope: data.subscription_scope,
            duration_min_seconds: data.duration_min_seconds,
            duration_max_seconds: data.duration_max_seconds,
            selector_mode: data.selector_mode,
          },
        });
        onSuccess();
      } else {
        const result = await createPipeline.mutateAsync({
          name: data.name,
          playlist_id: data.playlist_id,
          subscription_scope: data.subscription_scope,
          duration_min_seconds: data.duration_min_seconds,
          duration_max_seconds: data.duration_max_seconds,
          selector_mode: data.selector_mode,
          subscription_ids: data.subscription_ids,
          ignore_list_ids: [],
          selector_ids: [],
        });
        onSuccess(result.id);
      }
    } catch (err: any) {
      console.error('Failed to save pipeline:', err);
      
      // Extract error message from API response
      const message = err.response?.data?.detail || err.message || 'Failed to save pipeline';
      alert(`Error: ${message}`);
    }
  };

  const handlePreview = async () => {
    if (!pipeline?.id) return;
    
    try {
      const result = await mockPreview.mutateAsync({
        pipeline_id: pipeline.id,
        item_path: '',
      });
      setPreviewData(result);
      setPreviewOpen(true);
    } catch (err) {
      console.error('Failed to generate preview:', err);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Name and destination for this pipeline</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Pipeline Name *</Label>
              <Input
                id="name"
                {...register('name')}
                placeholder="e.g., Tech Reviews"
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="playlist_id">Destination Playlist *</Label>
              <Select
                value={watch('playlist_id') || ''}
                onValueChange={(value) => setValue('playlist_id', value || '')}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a playlist" />
                </SelectTrigger>
                <SelectContent>
                  {playlists?.map((playlist) => (
                    <SelectItem key={playlist.id} value={playlist.id}>
                      {playlist.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.playlist_id && (
                <p className="text-sm text-red-500 mt-1">{errors.playlist_id.message}</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Duration Filters</CardTitle>
            <CardDescription>Filter videos by duration (in seconds)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="duration_min">Minimum Duration (seconds)</Label>
                <Input
                  id="duration_min"
                  type="number"
                  {...register('duration_min_seconds', { valueAsNumber: true })}
                  placeholder="e.g., 60"
                />
              </div>
              <div>
                <Label htmlFor="duration_max">Maximum Duration (seconds)</Label>
                <Input
                  id="duration_max"
                  type="number"
                  {...register('duration_max_seconds', { valueAsNumber: true })}
                  placeholder="e.g., 3600"
                />
                {errors.duration_max_seconds && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.duration_max_seconds.message}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Subscription Scope</CardTitle>
            <CardDescription>Which subscriptions should this pipeline process?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="subscription_scope">Scope</Label>
              <Select
                value={subscriptionScope}
                onValueChange={(value) => setValue('subscription_scope', value as 'all' | 'selected')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Subscriptions</SelectItem>
                  <SelectItem value="selected">Selected Subscriptions</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {subscriptionScope === 'selected' && (
              <div className="p-4 border rounded-md bg-muted/50">
                <p className="text-sm text-muted-foreground mb-2">
                  Subscription selection will be available after creating the pipeline.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Word Filters</CardTitle>
            <CardDescription>Block videos containing these words (one per line)</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              {...register('blocked_words')}
              placeholder="Enter blocked words, one per line"
              rows={5}
            />
            <p className="text-sm text-muted-foreground mt-2">
              Note: Word filters are not yet implemented in the backend
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Selectors</CardTitle>
            <CardDescription>Advanced content selection rules</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 border rounded-md bg-muted/50">
              <p className="text-sm text-muted-foreground">
                Selector configuration is not yet implemented. This feature will allow you to
                define advanced rules for content selection.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between items-center pt-4">
          <div>
            {isEdit && (
              <Button
                type="button"
                variant="outline"
                onClick={handlePreview}
                disabled={mockPreview.isPending}
              >
                <Eye className="mr-2 h-4 w-4" />
                {mockPreview.isPending ? 'Loading...' : 'Preview'}
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : isEdit ? 'Update Pipeline' : 'Create Pipeline'}
            </Button>
          </div>
        </div>
      </form>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Pipeline Preview</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {previewData ? (
              <div className="space-y-2">
                <p className="text-sm">
                  <span className="font-medium">Action:</span> {previewData.action}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Reason:</span> {previewData.reason}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Filter:</span> {previewData.filter_name}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground">No preview data available</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

