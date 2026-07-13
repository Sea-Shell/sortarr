import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/pipelines/new')({
  component: CreatePipeline,
})

function CreatePipeline() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Create Pipeline</h1>
      <p className="text-gray-600 mt-2">Create pipeline placeholder</p>
    </div>
  )
}
