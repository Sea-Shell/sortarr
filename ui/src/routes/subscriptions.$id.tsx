import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/subscriptions/$id')({
  component: SubscriptionDetail,
})

function SubscriptionDetail() {
  const { id } = Route.useParams()
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Subscription Detail</h1>
      <p className="text-gray-600 mt-2">Subscription {id} placeholder</p>
    </div>
  )
}
