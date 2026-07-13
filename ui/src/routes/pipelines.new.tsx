import { createFileRoute, useNavigate } from '@tanstack/react-router';
import PipelineForm from '../components/PipelineForm';

export const Route = createFileRoute('/pipelines/new')({
  component: NewPipeline,
});

function NewPipeline() {
  const navigate = useNavigate();

  const handleSuccess = (id?: string) => {
    if (id) {
      navigate({ to: `/pipelines/${id}` });
    } else {
      navigate({ to: '/pipelines' });
    }
  };

  const handleCancel = () => {
    navigate({ to: '/pipelines' });
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Create Pipeline</h1>
      <PipelineForm onSuccess={handleSuccess} onCancel={handleCancel} />
    </div>
  );
}
