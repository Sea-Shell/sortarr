import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { usePipeline } from '../hooks/use-api';
import PipelineForm from '../components/PipelineForm';
import LoadingSkeleton from '../components/LoadingSkeleton';

export const Route = createFileRoute('/pipelines/$id')({
  component: EditPipeline,
});

function EditPipeline() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const { data: pipeline, isLoading, error } = usePipeline(id);

  const handleSuccess = () => {
    navigate({ to: '/pipelines' });
  };

  const handleCancel = () => {
    navigate({ to: '/pipelines' });
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Edit Pipeline</h1>
        <LoadingSkeleton count={1} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Edit Pipeline</h1>
        <div className="text-red-500">Error loading pipeline: {error.message}</div>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Edit Pipeline</h1>
        <div className="text-muted-foreground">Pipeline not found</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Edit Pipeline</h1>
      <PipelineForm
        pipeline={pipeline}
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
}
