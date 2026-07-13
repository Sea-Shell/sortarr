import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/pipelines')({
  component: PipelinesList,
})

function PipelinesList() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Pipelines</h1>
      <p className="text-gray-600 mt-2">Pipelines list placeholder</p>
    </div>
  )
}
