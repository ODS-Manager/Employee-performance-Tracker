import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { useAuthStore } from '../../store/authStore'
import { Button } from '../ui/button'
import { 
  ChevronRight, 
  ArrowLeft,
  Home,
  Users,
  FileText,
  BarChart3,
  Plus,
  Building2,
  TrendingUp,
  ClipboardCheck,
  Receipt,
  Target,
  CalendarDays,
  ChevronDown,
  CheckCircle2,
  Settings
} from 'lucide-react'

// Dropdown menu item type
interface DropdownItem {
  path: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
}

// Navigation item with optional dropdown
interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  dropdown?: DropdownItem[];
}

// Navigation items for quick access
const navItems: NavItem[] = [
  { path: '/admin/teams', label: 'Teams', icon: Users, description: 'View all teams' },
  { path: '/admin/examiners', label: 'Employees', icon: FileText, description: 'Employee reports' },
  { 
    path: '/admin/examiner-targets', 
    label: 'Targets', 
    icon: Target, 
    description: 'Weekly targets',
    dropdown: [
      { path: '/admin/examiner-targets', label: 'Employee Targets', icon: CheckCircle2 },
      { path: '/admin/team-lead-targets', label: 'Team Lead Targets', icon: CheckCircle2 },
    ]
  },
  { path: '/admin/orders', label: 'Orders', icon: BarChart3, description: 'Order analysis' },
  { path: '/admin/productivity', label: 'Productivity', icon: TrendingUp, description: 'Productivity reports' },
  { path: '/admin/quality-audit', label: 'Quality Audit', icon: ClipboardCheck, description: 'Quality audit reports' },
  { 
    path: '/admin/attendance/team-leads', 
    label: 'Attendance', 
    icon: CalendarDays, 
    description: 'Attendance management',
    dropdown: [
      { path: '/admin/attendance/team-leads', label: 'Mark Attendance', icon: CheckCircle2 },
      { path: '/admin/attendance/employees', label: 'Employee Attendance', icon: Users },
      { path: '/admin/attendance/monthly-report', label: 'Monthly Report', icon: CheckCircle2 },
    ]
  },
  { path: '/admin/billing', label: 'Billing', icon: Receipt, description: 'Billing reports' },
  { path: '/admin/reference-data', label: 'Reference Data', icon: Settings, description: 'Manage reference data' },
]

// Superadmin only nav items
const superadminNavItems: NavItem[] = [
  { path: '/admin/organizations', label: 'Centers', icon: Building2, description: 'Manage centers' },
]

// Route configuration for breadcrumbs
const routeConfig: Record<string, { label: string; parent?: string }> = {
  '/admin': { label: 'Admin' },
  '/admin/dashboard': { label: 'Dashboard', parent: '/admin' },
  '/admin/teams': { label: 'Teams', parent: '/admin/dashboard' },
  '/admin/examiners': { label: 'Employee Reports', parent: '/admin/dashboard' },
  '/admin/examiner-management': { label: 'Employee Management', parent: '/admin/examiners' },
  '/admin/examiner-targets': { label: 'Employee Targets', parent: '/admin/dashboard' },
  '/admin/orders': { label: 'Order Analysis', parent: '/admin/dashboard' },
  '/admin/onboarding': { label: 'Onboarding', parent: '/admin/dashboard' },
  '/admin/team-management': { label: 'Team Management', parent: '/admin/teams' },
  '/admin/score-management': { label: 'Score Management', parent: '/admin/team-management' },
  '/admin/quality-audit': { label: 'Quality Audit', parent: '/admin/dashboard' },
  '/admin/billing': { label: 'Billing Reports', parent: '/admin/dashboard' },
  '/admin/team-report': { label: 'Team Report', parent: '/admin/teams' },
  '/admin/organizations': { label: 'Centers', parent: '/admin/dashboard' },
  '/admin/productivity': { label: 'Productivity', parent: '/admin/dashboard' },
  '/admin/attendance': { label: 'Attendance', parent: '/admin/dashboard' },
  '/admin/attendance/team-leads': { label: 'Team Lead Attendance', parent: '/admin/attendance' },
  '/admin/attendance/employees': { label: 'Employee Attendance', parent: '/admin/attendance' },
  '/admin/attendance/monthly-report': { label: 'Monthly Report', parent: '/admin/attendance' },
  '/admin/team-lead-targets': { label: 'Team Lead Targets', parent: '/admin/examiner-targets' },
  '/admin/reference-data': { label: 'Reference Data', parent: '/admin/dashboard' },
}

// Function to get breadcrumb trail
const getBreadcrumbs = (pathname: string): { path: string; label: string }[] => {
  const breadcrumbs: { path: string; label: string }[] = []
  
  // Handle dynamic routes like /admin/team-report/:id
  let currentPath = pathname
  
  // Check for dynamic team report route
  if (pathname.startsWith('/admin/team-report/')) {
    currentPath = '/admin/team-report'
  }
  
  // Check for dynamic examiner performance route
  if (pathname.match(/^\/admin\/examiners\/\d+\/performance$/)) {
    currentPath = '/admin/examiners/:userId/performance'
    // Add to routeConfig dynamically if not present
    if (!routeConfig[currentPath]) {
      routeConfig[currentPath] = { label: 'Performance Report', parent: '/admin/examiner-management' }
    }
  }
  
  // Check for dynamic examiner detail route
  if (pathname.match(/^\/admin\/examiners\/\d+$/) && !pathname.includes('/performance')) {
    currentPath = '/admin/examiners/:userId'
    // Add to routeConfig dynamically if not present
    if (!routeConfig[currentPath]) {
      routeConfig[currentPath] = { label: 'Employee Details', parent: '/admin/examiner-management' }
    }
  }
  
  // Build breadcrumb trail
  let path: string | undefined = currentPath
  while (path) {
    const routeInfo: { label: string; parent?: string } | undefined = routeConfig[path]
    if (routeInfo) {
      breadcrumbs.unshift({ path, label: routeInfo.label })
      path = routeInfo.parent
    } else {
      break
    }
  }
  
  return breadcrumbs
}

// Dropdown component
const NavDropdown = ({ 
  item, 
  isActive 
}: { 
  item: NavItem; 
  isActive: (path: string) => boolean;
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const Icon = item.icon

  // Check if any dropdown item is active
  const isAnyDropdownItemActive = item.dropdown?.some(dropItem => isActive(dropItem.path))

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const handleToggle = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsOpen(!isOpen)
  }

  const handleItemClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsOpen(false)
  }

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <Button
        variant={isAnyDropdownItemActive ? "default" : "ghost"}
        size="sm"
        className="whitespace-nowrap flex items-center gap-1"
        onClick={handleToggle}
        type="button"
      >
        <Icon className="w-4 h-4" />
        {item.label}
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {isOpen && item.dropdown && (
        <div className="absolute top-full left-0 mt-1 min-w-[200px] bg-white rounded-md shadow-lg border border-slate-200 py-1 z-[100]">
          {item.dropdown.map((dropItem) => {
            const DropIcon = dropItem.icon
            return (
              <Link
                key={dropItem.path}
                to={dropItem.path}
                onClick={handleItemClick}
                className="block"
              >
                <div
                  className={`px-4 py-2 text-sm flex items-center gap-2 hover:bg-slate-100 cursor-pointer ${
                    isActive(dropItem.path) ? 'bg-slate-100 font-medium' : ''
                  }`}
                >
                  {DropIcon && <DropIcon className="w-4 h-4 text-slate-500 flex-shrink-0" />}
                  <span className="truncate">{dropItem.label}</span>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

export const AdminNav = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  
  const breadcrumbs = getBreadcrumbs(location.pathname)
  const isDashboard = location.pathname === '/admin/dashboard' || location.pathname === '/admin'
  
  // Superadmin should not see Add Order button
  const showAddOrderButton = user?.userRole !== 'superadmin'
  const isSuperadmin = user?.userRole === 'superadmin'

  const mainNavItems = isSuperadmin
    ? navItems.filter((item) => 
        item.path !== '/admin/examiner-targets' && 
        item.path !== '/admin/attendance/team-leads' && 
        item.path !== '/admin/reference-data'
      )
    : navItems
  
  // Combine nav items based on role
  const allNavItems = isSuperadmin ? [...mainNavItems, ...superadminNavItems] : mainNavItems
  
  // Determine the back path
  const getBackPath = () => {
    if (breadcrumbs.length > 1) {
      return breadcrumbs[breadcrumbs.length - 2].path
    }
    return '/admin/dashboard'
  }
  
  const handleBack = () => {
    // Try browser history first, fallback to parent route
    if (window.history.length > 2) {
      navigate(-1)
    } else {
      navigate(getBackPath())
    }
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="bg-white border-b border-slate-200">
      <div className="container mx-auto px-4">
        {/* Show navigation menu on dashboard, breadcrumbs on other pages */}
        {isDashboard ? (
          // Dashboard: Show main navigation with quick access
          <nav className="flex items-center justify-between py-3">
            <div className="flex items-center gap-1">
              {allNavItems.map((item) => {
                const Icon = item.icon
                
                if (item.dropdown) {
                  return (
                    <NavDropdown
                      key={item.path}
                      item={item}
                      isActive={isActive}
                    />
                  )
                }
                
                return (
                  <Link key={item.path} to={item.path}>
                    <Button 
                      variant={isActive(item.path) ? "default" : "ghost"}
                      size="sm"
                      className="whitespace-nowrap"
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Button>
                  </Link>
                )
              })}
            </div>
            
            {/* Primary CTA - Only show for non-superadmin */}
            {showAddOrderButton && (
              <Link to="/examiner/new-order">
                <Button size="sm" className="bg-green-600 hover:bg-green-700 whitespace-nowrap h-8">
                  <Plus className="w-4 h-4 mr-2" />
                  New Order
                </Button>
              </Link>
            )}
          </nav>
        ) : (
          // Other pages: Show breadcrumbs with back button
          <nav className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              {/* Back Button */}
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleBack}
                className="mr-2 hover:bg-slate-100"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
              
              {/* Separator */}
              <div className="h-5 w-px bg-slate-300 mr-2" />
              
              {/* Home Icon */}
              <Link 
                to="/admin/dashboard" 
                className="text-slate-500 hover:text-slate-900 transition-colors"
              >
                <Home className="w-4 h-4" />
              </Link>
              
              {/* Breadcrumbs */}
              {breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1
                const isFirst = index === 0 && crumb.path === '/admin'
                
                // Skip the /admin root in breadcrumbs display
                if (isFirst && crumb.label === 'Admin') {
                  return null
                }
                
                return (
                  <div key={crumb.path} className="flex items-center">
                    <ChevronRight className="w-4 h-4 text-slate-400 mx-1" />
                    {isLast ? (
                      <span className="text-sm font-medium text-slate-900">
                        {crumb.label}
                      </span>
                    ) : (
                      <Link 
                        to={crumb.path}
                        className="text-sm text-slate-500 hover:text-slate-900 transition-colors hover:underline"
                      >
                        {crumb.label}
                      </Link>
                    )}
                  </div>
                )
              })}
            </div>
            
            {/* Quick navigation links on inner pages */}
            <div className="hidden md:flex items-center gap-1">
              {mainNavItems.slice(0, 3).map((item) => {
                const Icon = item.icon
                return (
                  <Link key={item.path} to={item.path}>
                    <Button 
                      variant={isActive(item.path) ? "secondary" : "ghost"}
                      size="sm"
                      className="whitespace-nowrap text-xs"
                    >
                      <Icon className="w-3 h-3 mr-1" />
                      {item.label}
                    </Button>
                  </Link>
                )
              })}
            </div>
          </nav>
        )}
      </div>
    </div>
  )
}
