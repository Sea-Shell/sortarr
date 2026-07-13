function App() {
  return (
    <div className="bg-background text-text p-4 min-h-screen">
      <h1 className="text-headline-lg font-semibold">sortarr v2</h1>
      <p className="text-body-md text-text-muted mt-2">Dashboard-Centric Calm</p>
      
      {/* Test color tokens */}
      <div className="mt-6 space-y-2">
        <div className="bg-surface border border-border p-4 rounded-md">
          <p className="text-primary font-semibold">Primary color</p>
        </div>
        <div className="bg-surface border border-border p-4 rounded-md">
          <p className="text-success font-semibold">Success color</p>
        </div>
        <div className="bg-surface border border-border p-4 rounded-md">
          <p className="text-warning font-semibold">Warning color</p>
        </div>
        <div className="bg-surface border border-border p-4 rounded-md">
          <p className="text-error font-semibold">Error color</p>
        </div>
      </div>
    </div>
  )
}

export default App
