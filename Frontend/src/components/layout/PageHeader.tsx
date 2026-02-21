import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { getInitials, handleLogoutFlow } from '../../utils/helpers'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Avatar, AvatarFallback } from '../ui/avatar'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../ui/dropdown-menu'
import { ChangePasswordDialog } from '../common/ChangePasswordDialog'
import { HeaderRefreshButton } from '../common/HeaderRefreshButton'
import { 
  Settings,
  LogOut,
  Activity,
  Lock
} from 'lucide-react'
import odsLogo from '../../assets/ods-logo.png'

interface PageHeaderProps {
  title: string
  subtitle?: string
  children?: React.ReactNode
}

export function PageHeader({ 
  title, 
  subtitle,
  children
}: PageHeaderProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [changePasswordOpen, setChangePasswordOpen] = useState(false)

  const handleLogout = async () => {
    await handleLogoutFlow(logout, navigate)
  }

  const defaultSubtitle = subtitle ?? `Welcome back, ${user?.userName}!`

  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={odsLogo} alt="ODS Logo" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
                <p className="text-sm text-slate-600 mt-1">{defaultSubtitle}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Additional children (like filters) */}
              {children}

              <HeaderRefreshButton />

              <Badge variant="outline" className="px-3 py-1">
                <Activity className="w-3 h-3 mr-1" />
                {user?.userRole}
              </Badge>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                    <Avatar>
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        {getInitials(user?.userName || '')}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">{user?.userName}</p>
                      <p className="text-xs text-muted-foreground">@{user?.userName}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setChangePasswordOpen(true)}>
                    <Lock className="mr-2 h-4 w-4" />
                    Change Password
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Change Password Dialog */}
      <ChangePasswordDialog 
        open={changePasswordOpen} 
        onClose={() => setChangePasswordOpen(false)} 
      />
    </>
  )
}
