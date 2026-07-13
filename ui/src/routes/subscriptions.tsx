import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/subscriptions')({
  component: SubscriptionsList,
})

function SubscriptionsList() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Subscriptions</h1>
      <p className="text-gray-600 mt-2">Subscriptions list placeholder</p>
    </div>
  )
}
