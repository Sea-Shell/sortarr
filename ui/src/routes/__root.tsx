import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

export const Route = createRootRoute({
  component: () => (
    <div>
      {/* Temporary navigation for testing - will be replaced with Sidebar in Phase 2 */}
      <nav className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex gap-4">
          <Link to="/" className="text-blue-600 hover:underline">Dashboard</Link>
          <Link to="/subscriptions" className="text-blue-600 hover:underline">Subscriptions</Link>
          <Link to="/pipelines" className="text-blue-600 hover:underline">Pipelines</Link>
          <Link to="/runs" className="text-blue-600 hover:underline">Runs</Link>
          <Link to="/settings" className="text-blue-600 hover:underline">Settings</Link>
        </div>
      </nav>
      <Outlet />
      <TanStackRouterDevtools />
    </div>
  ),
})
