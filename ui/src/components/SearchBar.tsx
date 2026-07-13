import * as React from "react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { Search } from "lucide-react"

/**
 * Props for SearchBar component
 */
export interface SearchBarProps {
  /** Current search value */
  value: string
  /** Change handler with debounced value */
  onChange: (value: string) => void
  /** Placeholder text */
  placeholder?: string
  /** Debounce delay in milliseconds */
  debounceMs?: number
  /** Additional CSS classes */
  className?: string
}

/**
 * SearchBar with debounced input
 * 
 * @example
 * ```tsx
 * <SearchBar
 *   value={searchTerm}
 *   onChange={setSearchTerm}
 *   placeholder="Search videos..."
 * />
 * ```
 */
export const SearchBar = React.memo(function SearchBar({
  value,
  onChange,
  placeholder = "Search...",
  debounceMs = 300,
  className,
}: SearchBarProps) {
  const [localValue, setLocalValue] = React.useState(value)
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // Sync external value changes
  React.useEffect(() => {
    setLocalValue(value)
  }, [value])

  const handleChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setLocalValue(newValue)

    // Clear existing timeout
    if (timeoutRef.current !== undefined) {
      clearTimeout(timeoutRef.current)
    }

    // Set new timeout for debounced callback
    timeoutRef.current = setTimeout(() => {
      onChange(newValue)
    }, debounceMs)
  }, [onChange, debounceMs])

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return (
    <div className={cn("relative", className)}>
      <Search 
        className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" 
        aria-hidden="true"
      />
      <Input
        type="search"
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        className="pl-9"
        aria-label={placeholder}
      />
    </div>
  )
})

export default SearchBar
