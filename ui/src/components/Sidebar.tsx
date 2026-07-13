import { Link } from '@tanstack/react-router'
import { useState } from 'react'

interface NavItem {
  to: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/subscriptions', label: 'Subscriptions', icon: '📺' },
  { to: '/pipelines', label: 'Pipelines', icon: '⚙️' },
  { to: '/runs', label: 'Runs', icon: '▶️' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)

  const closeSidebar = () => setIsOpen(false)

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-[var(--color-surface)] border border-[var(--color-border)] hover:bg-[var(--color-background)]"
        aria-label="Toggle navigation"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          )}
        </svg>
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-30"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:static top-0 left-0 h-screen w-60 z-40
          bg-[var(--color-surface)] border-r border-[var(--color-border)]
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="px-4 py-6">
          <h1 className="text-xl font-semibold text-[var(--color-primary)]">
            sortarr
          </h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={closeSidebar}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-[var(--color-text)] hover:bg-[var(--color-background)] transition-colors"
              activeProps={{
                className: 'bg-[var(--color-background)] font-medium',
              }}
            >
              <span className="text-lg" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Quota gauge placeholder */}
        <div className="px-4 py-6 border-t border-[var(--color-border)]">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">API Quota</span>
              <span className="font-medium">45%</span>
            </div>
            <div className="h-2 bg-[var(--color-background)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--color-success)] transition-all duration-300"
                style={{ width: '45%' }}
                role="progressbar"
                aria-valuenow={45}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <p className="text-xs text-[var(--color-text-muted)]">
              4,500 / 10,000 units
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}
