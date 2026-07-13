import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/runs')({
  component: RunHistory,
})

function RunHistory() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Run History</h1>
      <p className="text-gray-600 mt-2">Run history placeholder</p>
    </div>
  )
}
