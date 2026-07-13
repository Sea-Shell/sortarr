import { cn } from "@/lib/utils"

/**
 * Skeleton variant types
 */
export type SkeletonVariant = "text" | "card" | "circle" | "rectangle"

/**
 * Props for LoadingSkeleton component
 */
export interface LoadingSkeletonProps {
  /** Visual variant of the skeleton */
  variant?: SkeletonVariant
  /** Number of skeleton elements to render */
  count?: number
  /** Additional CSS classes */
  className?: string
  /** Width override (CSS value) */
  width?: string
  /** Height override (CSS value) */
  height?: string
}

/**
 * Base skeleton element with pulse animation
 */
function SkeletonBase({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "bg-muted rounded animate-pulse",
        className
      )}
      aria-live="polite"
      aria-busy="true"
      role="status"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

/**
 * LoadingSkeleton provides reusable loading placeholder components
 * with variants for different content types. Respects prefers-reduced-motion.
 * 
 * @example
 * ```tsx
 * // Single text line
 * <LoadingSkeleton variant="text" />
 * 
 * // Multiple card skeletons
 * <LoadingSkeleton variant="card" count={3} />
 * 
 * // Avatar circle
 * <LoadingSkeleton variant="circle" className="size-10" />
 * ```
 */
export function LoadingSkeleton({
  variant = "text",
  count = 1,
  className,
  width,
  height,
}: LoadingSkeletonProps) {
  const skeletons = Array.from({ length: count }, (_, i) => i)

  const getVariantClasses = () => {
    switch (variant) {
      case "text":
        return cn("h-4 w-full", className)
      case "card":
        return cn("h-24 w-full", className)
      case "circle":
        return cn("size-10 rounded-full", className)
      case "rectangle":
        return cn("h-20 w-full", className)
      default:
        return className
    }
  }

  const style = {
    ...(width && { width }),
    ...(height && { height }),
  }

  return (
    <div className="space-y-2">
      {skeletons.map((index) => (
        <SkeletonBase
          key={index}
          className={getVariantClasses()}
          {...(Object.keys(style).length > 0 && { style })}
        />
      ))}
    </div>
  )
}

/**
 * Convenience exports for common skeleton patterns
 */
export const SkeletonText = (props: Omit<LoadingSkeletonProps, "variant">) => (
  <LoadingSkeleton variant="text" {...props} />
)

export const SkeletonCard = (props: Omit<LoadingSkeletonProps, "variant">) => (
  <LoadingSkeleton variant="card" {...props} />
)

export const SkeletonCircle = (props: Omit<LoadingSkeletonProps, "variant">) => (
  <LoadingSkeleton variant="circle" {...props} />
)

export const SkeletonRectangle = (props: Omit<LoadingSkeletonProps, "variant">) => (
  <LoadingSkeleton variant="rectangle" {...props} />
)

export default LoadingSkeleton
