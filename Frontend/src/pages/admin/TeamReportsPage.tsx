import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore } from '../../store/dashboardFilterStore'
import api, { teamsApi, metricsApi, productivityApi } from '../../services/api'
import type { TeamMetrics, TeamProductivity } from '../../types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { GlobalFilters } from '../../components/filters/GlobalFilters'
import { 
  Users, 
  Target, 
  Settings, 
  MapPin, 
  Package,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

// Interfaces matching the backend API response
interface TeamState {
  id: number
  teamId: number
  state: string
}

interface TeamProduct {
  id: number
  teamId: number
  productType: string
}

interface TeamMember {
  id: number
  userId: number
  userName: string
  userRole: string
  isActive: boolean
}

interface Team {
  id: number
  name: string
  orgId: number
  teamLeadId: number | null
  isActive: boolean
  states: TeamState[]
  products: TeamProduct[]
  members?: TeamMember[]
}

export const TeamReportsPage = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [teams, setTeams] = useState<Team[]>([])
  const [teamMetrics, setTeamMetrics] = useState<TeamMetrics[]>([])
  const [teamProductivity, setTeamProductivity] = useState<TeamProductivity[]>([])
  const [loading, setLoading] = useState(true)
  
  // Get filter state from store
  const {
    filterMonth,
    filterYear,
    filterOrgId,
  } = useDashboardFilterStore()

  useEffect(() => {
    if (!user || !['admin', 'superadmin'].includes(user.userRole)) {
      navigate('/login')
    } else {
      fetchData()
    }
  }, [user, navigate])

  // Re-fetch when filterOrgId or month/year filters change
  useEffect(() => {
    if (user) {
      fetchData()
    }
  }, [filterOrgId, filterMonth, filterYear])

  const fetchData = async () => {
    try {
      setLoading(true)
      const orgIdToFetch = user?.userRole === 'superadmin' 
        ? (filterOrgId ?? undefined) 
        : (user?.orgId ?? undefined)
      
      // Fetch teams
      const teamsResponse = await teamsApi.list({ orgId: orgIdToFetch, isActive: true })
      const teamsData = teamsResponse.items || []
      
      // Fetch member count for all teams
      const teamsWithMembers = await Promise.all(
        teamsData.map(async (team: Team) => {
          try {
            const members = await teamsApi.getMembers(team.id)
            return { ...team, members }
          } catch (error) {
            console.error(`Failed to fetch members for team ${team.id}:`, error)
            return { ...team, members: [] }
          }
        })
      )
      setTeams(teamsWithMembers)

      // Calculate start and end dates from filterMonth and filterYear
      const startDate = `${filterYear}-${filterMonth.padStart(2, '0')}-01`
      const lastDay = new Date(parseInt(filterYear), parseInt(filterMonth), 0).getDate()
      const endDate = `${filterYear}-${filterMonth.padStart(2, '0')}-${lastDay}`

      // Fetch team productivity for all teams
      const productivityData: TeamProductivity[] = []
      for (const team of teamsWithMembers) {
        try {
          const productivity = await productivityApi.getTeamProductivity({
            teamId: team.id,
            startDate,
            endDate,
          })
          productivityData.push(productivity)
        } catch (error) {
          console.error(`Failed to fetch productivity for team ${team.id}:`, error)
        }
      }
      setTeamProductivity(productivityData)

      // Fetch team metrics with month/year filter
      let metricsData: TeamMetrics[] = []
      try {
        const metricsResponse = await metricsApi.getTeamMetrics({ 
          orgId: orgIdToFetch,
          periodType: 'monthly',
          startDate,
          endDate,
        })
        metricsData = metricsResponse.items || []
        setTeamMetrics(metricsData)
      } catch (error) {
        console.error('Failed to fetch team metrics:', error)
        setTeamMetrics([])
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Calculate summary statistics
  const activeTeams = teams.filter(t => t.isActive).length
  const inactiveTeams = teams.filter(t => !t.isActive).length
  const totalMembers = teams.reduce((acc, t) => acc + (t.members?.length || 0), 0)
  const totalStates = new Set(teams.flatMap(t => t.states.map(s => s.state))).size
  const totalProducts = new Set(teams.flatMap(t => t.products.map(p => p.productType))).size

  // Prepare chart data - State coverage
  const stateCoverage: Record<string, number> = {}
  teams.forEach(team => {
    team.states.forEach(s => {
      stateCoverage[s.state] = (stateCoverage[s.state] || 0) + 1
    })
  })
  const stateChartData = Object.entries(stateCoverage)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([state, count]) => ({ name: state, teams: count }))

  // Prepare chart data - Product coverage (all products)
  const productCoverage: Record<string, number> = {}
  teams.forEach(team => {
    team.products.forEach(p => {
      productCoverage[p.productType] = (productCoverage[p.productType] || 0) + 1
    })
  })
  const productChartData = Object.entries(productCoverage)
    .sort((a, b) => b[1] - a[1]) // Sort by count descending
    .map(([product, count]) => ({ name: product, value: count }))

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Team Analytics" subtitle="Statistics and insights across all teams" />

      <AdminNav />

      <main className="container mx-auto px-4 py-8">
        {/* Action Buttons */}
        <div className="flex justify-end mb-6">
          <Button onClick={() => navigate('/admin/team-management')}>
            <Settings className="h-4 w-4 mr-2" />
            Manage Teams
          </Button>
        </div>

        {/* Filters Card */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <>
            {/* Key Metrics Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Teams</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{teams.length}</div>
                  <p className="text-xs text-muted-foreground">
                    {activeTeams} active, {inactiveTeams} inactive
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Members Across All Teams</CardTitle>
                  <Users className="h-4 w-4 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{totalMembers}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">State Coverage</CardTitle>
                  <MapPin className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{totalStates}</div>
                  <p className="text-xs text-muted-foreground">
                    Unique states covered
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Product Types</CardTitle>
                  <Package className="h-4 w-4 text-purple-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{totalProducts}</div>
                  <p className="text-xs text-muted-foreground">
                    Products handled
                  </p>
                </CardContent>
              </Card>
            </div>



            {/* Charts Row */}
            <div className="grid gap-6 md:grid-cols-2 mb-6">
              {/* State Coverage Chart */}
              <Card className="flex flex-col h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-5 w-5" />
                    Top States by Team Coverage
                  </CardTitle>
                  <CardDescription>Number of teams covering each state</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  {stateChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChart data={stateChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={100} />
                        <Tooltip />
                        <Bar dataKey="teams" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-[350px] text-muted-foreground">
                      No state coverage data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Product Coverage Chart */}
              <Card className="flex flex-col h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Product Distribution
                  </CardTitle>
                  <CardDescription>All {totalProducts} product types by number of teams</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  {productChartData.length > 0 ? (
                    <div className="h-[350px] overflow-y-auto pr-2">
                      <div className="grid grid-cols-2 gap-3">
                        {productChartData.map((product) => (
                          <div 
                            key={product.name}
                            className="relative flex flex-col p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200 hover:shadow-md transition-shadow"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <Package className="h-4 w-4 text-purple-600" />
                              <span className="text-xl font-bold text-purple-700">{product.value}</span>
                            </div>
                            <p className="text-xs font-medium text-slate-700 line-clamp-2" title={product.name}>
                              {product.name}
                            </p>
                            <p className="text-[10px] text-slate-500 mt-0.5">
                              {product.value === 1 ? 'team' : 'teams'}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-[350px] text-muted-foreground">
                      No product data available
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default TeamReportsPage
