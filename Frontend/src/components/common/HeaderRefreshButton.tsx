import { RefreshCw } from 'lucide-react'
import { Button } from '../ui/button'

export const HeaderRefreshButton = () => {
  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      className="h-8 w-8"
      onClick={handleRefresh}
      aria-label="Refresh page"
      title="Refresh page"
    >
      <RefreshCw className="h-3.5 w-3.5" />
    </Button>
  )
}
