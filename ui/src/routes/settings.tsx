import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/settings')({
  component: Settings,
})

function Settings() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="text-gray-600 mt-2">Settings placeholder</p>
    </div>
  )
}
