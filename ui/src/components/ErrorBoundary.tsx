import { Component, type ReactNode, type ErrorInfo } from "react"
import { Card, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

/**
 * Props for ErrorBoundary component
 */
export interface ErrorBoundaryProps {
  /** Child components to wrap */
  children: ReactNode
  /** Optional custom fallback component */
  fallback?: (error: Error, reset: () => void) => ReactNode
  /** Optional error handler callback */
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

/**
 * State for ErrorBoundary component
 */
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Default fallback UI for error boundary
 */
function DefaultErrorFallback({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  const isDev = import.meta.env.DEV

  return (
    <div className="flex items-center justify-center min-h-[400px] p-4">
      <Card className="max-w-2xl w-full border-l-4 border-l-[var(--color-error)]">
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="flex size-10 items-center justify-center rounded-full bg-[var(--color-error)]/10 flex-shrink-0">
              <AlertTriangle className="size-5 text-[var(--color-error)]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold mb-2">Something went wrong</h2>
              <p className="text-muted-foreground mb-4">
                An unexpected error occurred. Please try refreshing the page.
              </p>
              <div className="bg-muted p-3 rounded-md mb-4">
                <p className="font-mono text-sm break-words">{error.message}</p>
              </div>
              {isDev && error.stack && (
                <details className="mb-4">
                  <summary className="cursor-pointer text-sm font-medium mb-2">
                    Stack Trace
                  </summary>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
                    {error.stack}
                  </pre>
                </details>
              )}
              <Button onClick={reset} variant="default">
                Try Again
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
    </div>
  )
}

/**
 * ErrorBoundary catches React errors in child components and displays
 * a fallback UI. Logs errors to console in all environments and shows
 * stack traces in development mode.
 * 
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  resetErrorBoundary = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetErrorBoundary)
      }
      return (
        <DefaultErrorFallback
          error={this.state.error}
          reset={this.resetErrorBoundary}
        />
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
