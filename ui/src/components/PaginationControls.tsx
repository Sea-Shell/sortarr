import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"

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
export function PaginationControls({
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
    <div className={cn("flex items-center justify-between gap-4", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrevious}
        disabled={!canGoPrevious}
        className="gap-1"
      >
        <ChevronLeft className="size-4" />
        Previous
      </Button>

      <div className="text-sm text-muted-foreground">
        Page {currentPage} of {totalPages}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={handleNext}
        disabled={!canGoNext}
        className="gap-1"
      >
        Next
        <ChevronRight className="size-4" />
      </Button>
    </div>
  )
}

export default PaginationControls
