import { createFileRoute } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useConfig, useUpdateConfig, useAuthStatus, useLogout } from '@/hooks/use-api'
import { useTheme } from 'next-themes'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, LogIn, LogOut, Sun, Moon, Monitor } from 'lucide-react'
import { useState } from 'react'

export const Route = createFileRoute('/settings')({
  component: Settings,
})

const configSchema = z.object({
  schedule: z.string().min(1, 'Schedule is required'),
  reprocess_days: z.number().min(0, 'Must be 0 or greater'),
  activity_limit: z.number().min(0, 'Must be 0 or greater'),
  subscription_limit: z.number().min(0, 'Must be 0 or greater'),
  public_url: z.string().url('Must be a valid URL'),
})

type ConfigFormData = z.infer<typeof configSchema>

function Settings() {
  const { data: config, isLoading: configLoading, error: configError } = useConfig()
  const { data: authStatus, isLoading: authLoading } = useAuthStatus()
  const updateConfig = useUpdateConfig()
  const logout = useLogout()
  const { theme, setTheme } = useTheme()
  const [saveSuccess, setSaveSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<ConfigFormData>({
    resolver: zodResolver(configSchema),
    values: config ? {
      schedule: config.schedule || '0 */6 * * *',
      reprocess_days: config.reprocess_days || 2,
      activity_limit: config.activity_limit || 0,
      subscription_limit: config.subscription_limit || 0,
      public_url: config.public_url || 'http://localhost:8080',
    } : undefined,
  })

  const onSubmit = async (data: ConfigFormData) => {
    try {
      await updateConfig.mutateAsync(data)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      reset(data)
    } catch (err) {
      console.error('Failed to save config:', err)
    }
  }

  const handleLogout = async () => {
    if (confirm('Are you sure you want to log out?')) {
      await logout.mutateAsync()
    }
  }

  const handleLogin = () => {
    window.location.href = '/api/auth/login'
  }

  if (configError) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Settings</h1>
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          Failed to load config: {configError.message}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6">
        {/* Account Section */}
        <Card>
          <CardHeader>
            <CardTitle>YouTube Account</CardTitle>
            <CardDescription>Manage your YouTube OAuth connection</CardDescription>
          </CardHeader>
          <CardContent>
            {authLoading ? (
              <LoadingSkeleton variant="rectangle" className="h-20 w-full" />
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {authStatus?.authenticated ? (
                    <>
                      <CheckCircle className="size-5 text-[var(--color-success)]" />
                      <div>
                        <p className="font-medium">Connected</p>
                        <p className="text-sm text-muted-foreground">
                          Your YouTube account is connected
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <XCircle className="size-5 text-destructive" />
                      <div>
                        <p className="font-medium">Not Connected</p>
                        <p className="text-sm text-muted-foreground">
                          Connect your YouTube account to use Sortarr
                        </p>
                      </div>
                    </>
                  )}
                </div>
                {authStatus?.authenticated ? (
                  <Button
                    variant="outline"
                    onClick={handleLogout}
                    disabled={logout.isPending}
                  >
                    <LogOut className="size-4 mr-2" />
                    {logout.isPending ? 'Logging out...' : 'Logout'}
                  </Button>
                ) : (
                  <Button onClick={handleLogin}>
                    <LogIn className="size-4 mr-2" />
                    Connect YouTube
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Appearance Section */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Customize the UI theme</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label>Theme</Label>
              <div className="flex gap-2">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  onClick={() => setTheme('light')}
                  className="flex-1"
                >
                  <Sun className="size-4 mr-2" />
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => setTheme('dark')}
                  className="flex-1"
                >
                  <Moon className="size-4 mr-2" />
                  Dark
                </Button>
                <Button
                  variant={theme === 'system' ? 'default' : 'outline'}
                  onClick={() => setTheme('system')}
                  className="flex-1"
                >
                  <Monitor className="size-4 mr-2" />
                  Auto
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Configuration Form */}
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Configuration</CardTitle>
            <CardDescription>Configure pipeline schedule and limits</CardDescription>
          </CardHeader>
          <CardContent>
            {configLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map(i => (
                  <LoadingSkeleton key={i} variant="rectangle" className="h-16 w-full" />
                ))}
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Schedule */}
                <div className="space-y-2">
                  <Label htmlFor="schedule">Schedule (Cron Expression)</Label>
                  <Input
                    id="schedule"
                    {...register('schedule')}
                    placeholder="0 */6 * * *"
                  />
                  {errors.schedule && (
                    <p className="text-sm text-destructive">{errors.schedule.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Default: 0 */6 * * * (every 6 hours)
                  </p>
                </div>

                {/* Reprocess Days */}
                <div className="space-y-2">
                  <Label htmlFor="reprocess_days">Reprocess Days</Label>
                  <Input
                    id="reprocess_days"
                    type="number"
                    {...register('reprocess_days', { valueAsNumber: true })}
                    placeholder="2"
                  />
                  {errors.reprocess_days && (
                    <p className="text-sm text-destructive">{errors.reprocess_days.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Days back for title similarity comparison
                  </p>
                </div>

                {/* Activity Limit */}
                <div className="space-y-2">
                  <Label htmlFor="activity_limit">Activity Limit</Label>
                  <Input
                    id="activity_limit"
                    type="number"
                    {...register('activity_limit', { valueAsNumber: true })}
                    placeholder="0"
                  />
                  {errors.activity_limit && (
                    <p className="text-sm text-destructive">{errors.activity_limit.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Max activities per subscription (0 = unlimited)
                  </p>
                </div>

                {/* Subscription Limit */}
                <div className="space-y-2">
                  <Label htmlFor="subscription_limit">Subscription Limit</Label>
                  <Input
                    id="subscription_limit"
                    type="number"
                    {...register('subscription_limit', { valueAsNumber: true })}
                    placeholder="0"
                  />
                  {errors.subscription_limit && (
                    <p className="text-sm text-destructive">{errors.subscription_limit.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Max subscriptions to fetch (0 = unlimited)
                  </p>
                </div>

                {/* Public URL */}
                <div className="space-y-2">
                  <Label htmlFor="public_url">Public URL</Label>
                  <Input
                    id="public_url"
                    {...register('public_url')}
                    placeholder="http://localhost:8080"
                  />
                  {errors.public_url && (
                    <p className="text-sm text-destructive">{errors.public_url.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Public-facing URL for OAuth callback
                  </p>
                </div>

                {/* Submit Button */}
                <div className="flex items-center gap-3 pt-4">
                  <Button
                    type="submit"
                    disabled={!isDirty || updateConfig.isPending}
                  >
                    {updateConfig.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                  {saveSuccess && (
                    <span className="text-sm text-[var(--color-success)] flex items-center gap-1">
                      <CheckCircle className="size-4" />
                      Settings saved successfully
                    </span>
                  )}
                  {updateConfig.error && (
                    <span className="text-sm text-destructive">
                      Failed to save: {updateConfig.error.message}
                    </span>
                  )}
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}




