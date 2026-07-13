import { createRootRoute, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { Sidebar } from '../components/Sidebar'
import { ThemeProvider } from '../components/theme-provider'
import { ErrorBoundary } from '../components/ErrorBoundary'

export const Route = createRootRoute({
  component: () => (
    <ErrorBoundary>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        {/* Skip to main content link for keyboard navigation */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          Skip to main content
        </a>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main id="main-content" className="flex-1 overflow-y-auto" tabIndex={-1}>
            <Outlet />
          </main>
          <TanStackRouterDevtools />
        </div>
      </ThemeProvider>
    </ErrorBoundary>
  ),
})
