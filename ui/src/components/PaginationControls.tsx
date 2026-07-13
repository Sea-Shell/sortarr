import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { memo } from "react"

/**
 * Props for PaginationControls component
 */
export interface PaginationControlsProps {
  /** Current page (1-indexed) */
  currentPage: number
  /** Total number of pages */
  totalPages: number
  /** Callback when page changes */
  onPageChange: (page: number) => void
  /** Additional CSS classes */
  className?: string
}

/**
 * PaginationControls for navigating pages
 * Memoized for performance optimization
 * 
 * @example
 * ```tsx
 * <PaginationControls
 *   currentPage={page}
 *   totalPages={10}
 *   onPageChange={setPage}
 * />
 * ```
 */
export const PaginationControls = memo(function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
  className,
}: PaginationControlsProps) {
  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  const handlePrevious = () => {
    if (canGoPrevious) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNext = () => {
    if (canGoNext) {
      onPageChange(currentPage + 1)
    }
  }

  return (
    <nav 
      className={cn("flex items-center justify-between gap-4", className)}
      aria-label="Pagination navigation"
    >
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrevious}
        disabled={!canGoPrevious}
        className="gap-1"
        aria-label="Go to previous page"
      >
        <ChevronLeft className="size-4" aria-hidden="true" />
        Previous
      </Button>

      <div className="text-sm text-muted-foreground" aria-live="polite" aria-atomic="true">
        Page {currentPage} of {totalPages}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={handleNext}
        disabled={!canGoNext}
        className="gap-1"
        aria-label="Go to next page"
      >
        Next
        <ChevronRight className="size-4" aria-hidden="true" />
      </Button>
    </nav>
  )
})

export default PaginationControls
