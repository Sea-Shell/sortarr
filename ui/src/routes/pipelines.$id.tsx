import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/pipelines/$id')({
  component: EditPipeline,
})

function EditPipeline() {
  const { id } = Route.useParams()
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Edit Pipeline</h1>
      <p className="text-gray-600 mt-2">Edit pipeline {id} placeholder</p>
    </div>
  )
}
