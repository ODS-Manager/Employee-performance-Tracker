import { useEffect, useState, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore } from '../../store/dashboardFilterStore'
import { usersApi, organizationsApi } from '../../services/api'
import { hasAnyUserRole, isUserRole } from '../../utils/helpers'
import type { Organization, User } from '../../types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Button } from '../../components/ui/button'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { 
  Users, 
  UserCheck, 
  TrendingUp, 
  Settings,
  Activity,
  BarChart3,
  PieChart,
  Filter
} from 'lucide-react'
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts'

// Trend data interfaces
interface TrendData {
  month: string
  hired: number
  left: number
  active: number
}

interface RoleDistribution {
  name: string
  value: number
  color: string
  [key: string]: string | number  // Index signature for recharts compatibility
}

export const ExaminerReportsPage = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [examiners, setExaminers] = useState<User[]>([])
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)

  // Get filter state from store
  const {
    filterMonth,
    filterYear,
    filterOrgId,
  } = useDashboardFilterStore()

  useEffect(() => {
    if (!user || !hasAnyUserRole(user.userRole, ['admin', 'superadmin'])) {
      navigate('/login')
    } else {
      fetchData()
    }
  }, [user, navigate, location.key])

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch examiners and organizations in parallel
      const [usersRes, orgsRes] = await Promise.all([
        usersApi.list(),
        organizationsApi.list({ isActive: true }),
      ])
      
      // Filter out superadmin from the list (they're not regular examiners)
      const filteredExaminers = (usersRes.items || []).filter((u: User) => 
        !isUserRole(u.userRole, 'superadmin')
      )
      setExaminers(filteredExaminers)
      setOrganizations(orgsRes.items || [])
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Filter examiners based on selected filters
  const filteredExaminers = useMemo(() => {
    let filtered = [...examiners]
    
    // Apply organization filter
    if (filterOrgId) {
      const orgId = parseInt(filterOrgId)
      filtered = filtered.filter(emp => emp.orgId === orgId)
    }
    
    // Apply date range filter based on filter month/year
    if (filterMonth && filterYear) {
      const filterDate = new Date(parseInt(filterYear), parseInt(filterMonth) - 1, 1)
      const nextMonth = new Date(filterDate.getFullYear(), filterDate.getMonth() + 1, 1)
      
      filtered = filtered.filter(emp => {
        if (!emp.createdAt) return false
        
        const empCreateDate = new Date(emp.createdAt)
        
        // Examiner must have been created before or during the filter month
        // and still be active in that month (not deactivated before the filter month)
        const wasCreatedBeforeOrDuring = empCreateDate < nextMonth
        const wasStillActiveInMonth = !emp.deactivatedAt || new Date(emp.deactivatedAt) >= filterDate
        
        return wasCreatedBeforeOrDuring && wasStillActiveInMonth
      })
    }
    
    return filtered
  }, [examiners, filterOrgId, filterMonth, filterYear])

  // Check if filters are active
  const hasActiveFilters = !!filterOrgId || (filterMonth && filterYear)
  
  // Get organization name for display
  const getOrgName = (orgId: string): string => {
    const org = organizations.find(o => o.id.toString() === orgId)
    return org?.name || 'Unknown Organization'
  }

  // Calculate stats from filtered examiners
  const activeCount = filteredExaminers.filter(e => e.isActive).length
  const activeExaminers = filteredExaminers.filter(e => e.isActive)
  const adminCount = activeExaminers.filter(e => isUserRole(e.userRole, 'admin')).length
  const teamLeadCount = activeExaminers.filter(e => isUserRole(e.userRole, 'team_lead')).length
  const examinerCount = activeExaminers.filter(e => isUserRole(e.userRole, 'examiner')).length

  // Generate trend data based on actual examiner creation dates
  const generateTrendData = (): TrendData[] => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const basePeriods = 6 // Default to 6 months
    
    // Get the date range based on selected period
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth()
    
    const data: TrendData[] = []
    
    // Create maps to count hires and departures per month
    const hiresByMonth: Map<string, number> = new Map()
    const leftByMonth: Map<string, number> = new Map()
    
    // Find the earliest examiner creation date
    let earliestDate: Date | null = null
    
    filteredExaminers.forEach(emp => {
      // Track hires by createdAt
      if (emp.createdAt) {
        const createdDate = new Date(emp.createdAt)
        const hireKey = `${createdDate.getFullYear()}-${createdDate.getMonth()}`
        hiresByMonth.set(hireKey, (hiresByMonth.get(hireKey) || 0) + 1)
        
        if (!earliestDate || createdDate < earliestDate) {
          earliestDate = createdDate
        }
      }
      
      // Track departures by deactivatedAt (if available) or count inactive users without deactivatedAt in current month
      if (emp.deactivatedAt) {
        const deactivatedDate = new Date(emp.deactivatedAt)
        const leftKey = `${deactivatedDate.getFullYear()}-${deactivatedDate.getMonth()}`
        leftByMonth.set(leftKey, (leftByMonth.get(leftKey) || 0) + 1)
        
        // Also consider deactivation date for earliest date calculation
        if (!earliestDate || deactivatedDate < earliestDate) {
          earliestDate = deactivatedDate
        }
      } else if (!emp.isActive) {
        // For inactive users without deactivatedAt, count them in the current month
        // (these are users who were deactivated before we added the deactivatedAt tracking)
        const leftKey = `${currentYear}-${currentMonth}`
        leftByMonth.set(leftKey, (leftByMonth.get(leftKey) || 0) + 1)
      }
    })
    
    // Use the base period (6 months)
    const actualPeriods = basePeriods
    
    // Calculate running active count
    let runningActive = 0
    
    // Go through each month in the period
    for (let i = actualPeriods - 1; i >= 0; i--) {
      let targetMonth = currentMonth - i
      let targetYear = currentYear
      
      // Handle year rollover
      while (targetMonth < 0) {
        targetMonth += 12
        targetYear -= 1
      }
      
      const key = `${targetYear}-${targetMonth}`
      const hired = hiresByMonth.get(key) || 0
      const left = leftByMonth.get(key) || 0
      
      runningActive += hired - left
      
      data.push({
        month: `${months[targetMonth]}${targetYear !== currentYear ? " '" + targetYear.toString().slice(-2) : ''}`,
        hired,
        left,
        active: runningActive
      })
    }
    
    return data
  }

  const trendData = generateTrendData()

  // Role distribution for pie chart
  const roleDistribution: RoleDistribution[] = [
    { name: 'Examiner', value: examinerCount, color: '#22c55e' },
    { name: 'Team Leads', value: teamLeadCount, color: '#3b82f6' },
    { name: 'Admins', value: adminCount, color: '#8b5cf6' },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Employee Reports" subtitle="Analyze employee headcount and distribution" />
      <AdminNav />
      
      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Header with Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Employee Reports</h1>
            <p className="text-slate-600 mt-1">
              Analyze employee headcount and distribution
            </p>
          </div>
          <Button 
            onClick={() => navigate('/admin/examiner-management')}
            variant="outline"
          >
            <Settings className="h-4 w-4 mr-2" />
            Manage Employees
          </Button>
        </div>

        {/* Active Filters Indicator */}
        {hasActiveFilters && (
          <div className="flex items-center gap-2 mb-4">
            <Filter className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-600 font-medium">Active filters:</span>
            {filterOrgId && (
              <Badge variant="secondary" className="text-xs">
                Organization: {getOrgName(filterOrgId)}
              </Badge>
            )}
            {filterMonth && filterYear && (
              <Badge variant="secondary" className="text-xs">
                Period: {new Date(parseInt(filterYear), parseInt(filterMonth) - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
              </Badge>
            )}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {hasActiveFilters ? 'Filtered Employees' : 'Total Employees'}
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{filteredExaminers.length}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {hasActiveFilters ? `Filtered from ${examiners.length} total` : 'Across all roles'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active</CardTitle>
              <UserCheck className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{activeCount}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {((activeCount / Math.max(filteredExaminers.length, 1)) * 100).toFixed(0)}% of {hasActiveFilters ? 'filtered' : 'workforce'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          {/* Headcount Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Headcount Trend
              </CardTitle>
              <CardDescription>
                Monthly active employee count
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="active" 
                      stroke="#3b82f6" 
                      fill="#93c5fd" 
                      name="Active Employees"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Hiring vs Attrition */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Hiring vs Attrition
              </CardTitle>
              <CardDescription>
                Monthly employee movement
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="hired" fill="#22c55e" name="Hired" />
                    <Bar dataKey="left" fill="#ef4444" name="Left" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Second Charts Row */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          {/* Role Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Role Distribution
              </CardTitle>
              <CardDescription>
                Breakdown by role type
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-[250px]">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <RechartsPieChart>
                      <Pie
                        data={roleDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {roleDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-4 mt-2">
                    {roleDistribution.map((item) => (
                      <div key={item.name} className="flex items-center gap-2 text-sm">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-muted-foreground">{item.name}: {item.value}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Performance Metrics - Empty for now to complete the 3-column layout */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Quick Stats
              </CardTitle>
              <CardDescription>
                Key employee metrics
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Admins</span>
                  <Badge variant="secondary">{adminCount}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Team Leads</span>
                  <Badge variant="secondary">{teamLeadCount}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Examiner</span>
                  <Badge variant="secondary">{examinerCount}</Badge>
                </div>
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-sm font-medium">Total Active</span>
                  <Badge className="bg-green-600">{activeCount}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ExaminerReportsPage
