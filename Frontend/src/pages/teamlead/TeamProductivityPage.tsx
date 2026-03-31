import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, addDays, subDays } from 'date-fns'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore } from '../../store/dashboardFilterStore'
import { useTeamLeadFilterStore } from '../../store/teamLeadFilterStore'
import { teamsApi, productivityApi, weeklyTargetsApi } from '../../services/api'
import type { TeamProductivity, ExaminerProductivity } from '../../types'
import { getInitials, handleLogoutFlow } from '../../utils/helpers'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Progress } from '../../components/ui/progress'
import { Label } from '../../components/ui/label'
import { Input } from '../../components/ui/input'
import { Button } from '../../components/ui/button'
import { TeamLeadNav } from '../../components/layout/TeamLeadNav'
import { HeaderRefreshButton } from '../../components/common/HeaderRefreshButton'
import { GlobalFilters } from '../../components/filters/GlobalFilters'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../../components/ui/dropdown-menu'
import { 
  TrendingUp, 
  Award,

  LogOut,
  Loader2,
  Users,
  CalendarIcon,
  Shield,
  Filter,
  Target,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import odsLogo from '../../assets/ods-logo.png'

export const TeamProductivityPage = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { filterMonth, filterYear } = useDashboardFilterStore()
  const { selectedTeamId, setSelectedTeamId } = useTeamLeadFilterStore()
  
  // Set Target Dialog state
  const [targetDialogOpen, setTargetDialogOpen] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<ExaminerProductivity | null>(null)
  const [targetValue, setTargetValue] = useState<string>('')
  const [selectedWeekStart, setSelectedWeekStart] = useState<string>(() => {
    const today = new Date()
    const dayOfWeek = today.getDay() // 0=Sunday
    const sunday = new Date(today)
    sunday.setDate(today.getDate() - dayOfWeek)
    return format(sunday, 'yyyy-MM-dd')
  })

  // Calculate current week's Sunday for weekly target
  const getCurrentWeekStart = () => {
    const today = new Date()
    const dayOfWeek = today.getDay() // 0=Sunday
    const sunday = new Date(today)
    sunday.setDate(today.getDate() - dayOfWeek)
    return format(sunday, 'yyyy-MM-dd')
  }

  // Format week range for display
  const formatWeekRange = (weekStart: string) => {
    const start = new Date(weekStart)
    const end = addDays(start, 6)
    return `${format(start, 'MMM dd')} - ${format(end, 'MMM dd, yyyy')}`
  }

  // Navigate weeks in dialog
  const navigateDialogWeek = (direction: 'prev' | 'next') => {
    const current = new Date(selectedWeekStart)
    const newDate = direction === 'prev' 
      ? subDays(current, 7) 
      : addDays(current, 7)
    setSelectedWeekStart(format(newDate, 'yyyy-MM-dd'))
  }

  // Redirect if not team lead
  if (!user || user.userRole !== 'team_lead') {
    navigate('/login')
    return null
  }

  // Get all teams the team lead manages
  const { data: teamsData, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams', 'my-teams', user?.id],
    queryFn: () => teamsApi.myTeams(),
    enabled: !!user && user.userRole === 'team_lead',
  })

  const myTeams = teamsData?.items || []
  
  // Auto-select first team if none selected or selected team is not in the list
  const teamId = selectedTeamId && myTeams.some(t => t.id === selectedTeamId) 
    ? selectedTeamId 
    : myTeams[0]?.id || null

  // Update selected team if it changes
  useEffect(() => {
    if (teamId && teamId !== selectedTeamId) {
      setSelectedTeamId(teamId)
    }
  }, [teamId, selectedTeamId, setSelectedTeamId])

  // Calculate date range based on filter month/year
  const startDate = `${filterYear}-${filterMonth.padStart(2, '0')}-01`
  const lastDay = new Date(parseInt(filterYear), parseInt(filterMonth), 0).getDate()
  const endDate = `${filterYear}-${filterMonth.padStart(2, '0')}-${lastDay}`

  // Fetch team productivity
  const { data: teamProductivity, isLoading: loadingProductivity } = useQuery<TeamProductivity>({
    queryKey: ['productivity', 'team', teamId, startDate, endDate],
    queryFn: () => productivityApi.getTeamProductivity({
      teamId: teamId!,
      startDate,
      endDate,
    }),
    enabled: !!teamId,
  })

  const currentTeam = myTeams.find(t => t.id === teamId)

  // Mutation to save weekly target for individual examiner
  const saveTargetMutation = useMutation({
    mutationFn: (data: { teamId: number; userId: number; target: number; weekStartDate: string }) =>
      weeklyTargetsApi.setTeamTargets(data.teamId, {
        weekStartDate: data.weekStartDate,
        targets: [{ userId: data.userId, target: data.target }],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weeklyTargets'] })
      queryClient.invalidateQueries({ queryKey: ['productivity'] })
      toast.success('Weekly target saved successfully')
      setTargetDialogOpen(false)
      setSelectedEmployee(null)
      setTargetValue('')
      // Reset to current week for next time
      setSelectedWeekStart(getCurrentWeekStart())
    },
    onError: () => {
      toast.error('Failed to save target')
    },
  })

  // Fetch existing target for selected employee and week
  const { data: weeklyTargetData, isLoading: loadingWeeklyTarget } = useQuery({
    queryKey: ['weeklyTargets', teamId, selectedWeekStart, selectedEmployee?.userId],
    queryFn: () => weeklyTargetsApi.getTeamTargets({
      teamId: teamId!,
      weekStartDate: selectedWeekStart,
    }),
    enabled: !!teamId && !!selectedEmployee && targetDialogOpen,
  })

  // Get existing target for selected employee from the fetched data
  const existingTarget = weeklyTargetData?.members.find(
    m => m.userId === selectedEmployee?.userId
  )?.currentTarget

  // Update target value when existing target is loaded or week changes
  useEffect(() => {
    if (targetDialogOpen && existingTarget !== undefined && existingTarget !== null) {
      setTargetValue(existingTarget.toString())
    } else if (targetDialogOpen && !loadingWeeklyTarget && (existingTarget === undefined || existingTarget === null)) {
      setTargetValue('')
    }
  }, [existingTarget, targetDialogOpen, loadingWeeklyTarget, selectedWeekStart])

  // Handle opening the target dialog
  const handleOpenTargetDialog = (employee: ExaminerProductivity) => {
    setSelectedEmployee(employee)
    setTargetValue('')
    // Reset to current week when opening
    setSelectedWeekStart(getCurrentWeekStart())
    setTargetDialogOpen(true)
  }

  // Handle saving the target
  const handleSaveTarget = () => {
    if (!teamId || !selectedEmployee) return
    const target = parseInt(targetValue) || 0
    if (target <= 0) {
      toast.error('Please enter a valid target value')
      return
    }
    saveTargetMutation.mutate({
      teamId,
      userId: selectedEmployee.userId,
      target,
      weekStartDate: selectedWeekStart,
    })
  }

  const handleLogout = async () => {
    await handleLogoutFlow(logout, navigate)
  }

  const getProductivityColor = (percent: number | null) => {
    if (percent === null) return 'text-gray-500'
    if (percent >= 100) return 'text-green-600'
    if (percent >= 80) return 'text-blue-600'
    if (percent >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getProductivityBgColor = (percent: number | null) => {
    if (percent === null) return 'bg-gray-100'
    if (percent >= 100) return 'bg-green-100'
    if (percent >= 80) return 'bg-blue-100'
    if (percent >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  // Sort examiners by productivity for table (null values at the end)
  const sortedExaminers = [...(teamProductivity?.examiners || [])].sort(
    (a, b) => {
      if (a.productivityPercent === null && b.productivityPercent === null) return 0
      if (a.productivityPercent === null) return 1
      if (b.productivityPercent === null) return -1
      return b.productivityPercent - a.productivityPercent
    }
  )

  // Get month name for display
  const getDateRangeDisplay = () => {
    const monthName = new Date(parseInt(filterYear), parseInt(filterMonth) - 1).toLocaleString('default', { month: 'long' })
    return `${monthName} ${filterYear}`
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={odsLogo} alt="ODS Logo" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Team Productivity</h1>
                <p className="text-sm text-slate-600">
                  {currentTeam?.name || 'Loading...'} - {getDateRangeDisplay()}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <GlobalFilters showOrgFilter={false} />
              <HeaderRefreshButton />

              <Badge variant="outline" className="px-3 py-1">
                <Shield className="w-3 h-3 mr-1" />
                Team Lead
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

      {/* Navigation */}
      <TeamLeadNav />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Filters Card */}
        <Card className="mb-6 overflow-visible relative z-10">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 mb-3">
              <Filter className="h-4 w-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Filters</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Team Filter */}
              {myTeams.length > 0 && (
                <div className="space-y-1">
                  <Label className="text-xs text-slate-500">Team</Label>
                  <Select 
                    value={teamId?.toString() || ''} 
                    onValueChange={(value) => setSelectedTeamId(parseInt(value))}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder="Select team" />
                    </SelectTrigger>
                    <SelectContent>
                      {myTeams.map((team) => (
                        <SelectItem key={team.id} value={team.id.toString()}>
                          {team.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {loadingTeams || loadingProductivity ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : !teamId ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">You are not currently leading any team.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Team Productivity
                  </CardTitle>
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${getProductivityColor(teamProductivity?.teamProductivityPercent || 0)}`}>
                    {Math.round(teamProductivity?.teamProductivityPercent || 0)}%
                  </div>
                  <Progress 
                    value={Math.min(teamProductivity?.teamProductivityPercent || 0, 100)} 
                    className="mt-2 h-2"
                  />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Total Score
                  </CardTitle>
                  <Award className="h-5 w-5 text-purple-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">
                    {teamProductivity?.totalTeamScore?.toFixed(1) || '0'}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Target: {teamProductivity?.totalExpectedTarget?.toFixed(1) || '0'}
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Active Members
                  </CardTitle>
                  <Users className="h-5 w-5 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">
                    {teamProductivity?.activeMembers || 0}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Working Days
                  </CardTitle>
                  <CalendarIcon className="h-5 w-5 text-orange-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">
                    {teamProductivity?.period?.workingDays || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Weekly targets per examiner
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Employee Productivity Table */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Individual Performance</CardTitle>
                    <CardDescription>Detailed productivity breakdown for each team member</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rank</TableHead>
                      <TableHead>Employee</TableHead>
                      <TableHead className="text-center">Step 1</TableHead>
                      <TableHead className="text-center">Step 2</TableHead>
                      <TableHead className="text-center">Single Seat</TableHead>
                      <TableHead className="text-right">Total Score</TableHead>
                      <TableHead className="text-right">Target</TableHead>
                      <TableHead className="text-right">Productivity</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedExaminers.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={11} className="text-center py-12 text-muted-foreground">
                          No productivity data available
                        </TableCell>
                      </TableRow>
                    ) : (
                      sortedExaminers.map((examiner: ExaminerProductivity, index: number) => (
                        <TableRow key={examiner.userId}>
                          <TableCell>
                            <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                              index === 0 ? 'bg-yellow-100 text-yellow-800' :
                              index === 1 ? 'bg-slate-200 text-slate-700' :
                              index === 2 ? 'bg-orange-100 text-orange-800' :
                              'bg-slate-100 text-slate-600'
                            }`}>
                              {index + 1}
                            </div>
                          </TableCell>
                          <TableCell className="font-medium">
                            <div 
                              className="flex items-center gap-3 cursor-pointer hover:text-primary transition-colors"
                              onClick={() => navigate(`/teamlead/examiner/${examiner.userId}/performance`)}
                            >
                              <Avatar className="h-8 w-8">
                                <AvatarFallback>
                                  {getInitials(examiner.userName || '')}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <div>{examiner.userName || examiner.userName}</div>
                                <div className="text-xs text-muted-foreground">
                                  {examiner.employeeId}
                                </div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="text-sm">
                              <span className="font-medium">{examiner.completions.step1Only}</span>
                              <span className="text-muted-foreground ml-1">
                                ({examiner.scores.step1Score.toFixed(1)})
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="text-sm">
                              <span className="font-medium">{examiner.completions.step2Only}</span>
                              <span className="text-muted-foreground ml-1">
                                ({examiner.scores.step2Score.toFixed(1)})
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="text-sm">
                              <span className="font-medium">{examiner.completions.singleSeat}</span>
                              <span className="text-muted-foreground ml-1">
                                ({examiner.scores.singleSeatScore.toFixed(1)})
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {examiner.scores.totalScore.toFixed(1)}
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground">
                            {examiner.expectedTarget.toFixed(1)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge 
                              variant="outline"
                              className={`${getProductivityBgColor(examiner.productivityPercent)} ${getProductivityColor(examiner.productivityPercent)}`}
                            >
                              {examiner.productivityPercent !== null 
                                ? `${Math.round(examiner.productivityPercent)}%`
                                : 'N/A'
                              }
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenTargetDialog(examiner)}
                            >
                              <Target className="h-4 w-4 mr-1" />
                              Set Target
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Set Target Dialog */}
      <Dialog open={targetDialogOpen} onOpenChange={setTargetDialogOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Set Weekly Target
            </DialogTitle>
            <DialogDescription>
              Set the weekly productivity target for {selectedEmployee?.userName || selectedEmployee?.userName}.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {/* Week Selector */}
            <div className="flex items-center justify-center gap-2 p-3 bg-slate-50 rounded-lg">
              <Button 
                variant="outline" 
                size="icon" 
                className="h-8 w-8"
                onClick={() => navigateDialogWeek('prev')}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="text-sm font-medium min-w-[180px] text-center">
                <div className="flex items-center justify-center gap-2">
                  <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                  {formatWeekRange(selectedWeekStart)}
                </div>
                {selectedWeekStart === getCurrentWeekStart() && (
                  <Badge variant="secondary" className="mt-1 text-xs">Current Week</Badge>
                )}
              </div>
              <Button 
                variant="outline" 
                size="icon" 
                className="h-8 w-8"
                onClick={() => navigateDialogWeek('next')}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Loading State */}
            {loadingWeeklyTarget ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading target...</span>
              </div>
            ) : (
              <>
                {/* Existing Target Display */}
                {existingTarget !== undefined && existingTarget !== null && (
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <span className="text-sm text-blue-700">Current target for this week:</span>
                    <Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-300">
                      {existingTarget}
                    </Badge>
                  </div>
                )}

                {/* Target Input */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="newTarget" className="text-right">
                    {existingTarget !== undefined && existingTarget !== null ? 'New Target' : 'Weekly Target'}
                  </Label>
                  <Input
                    id="newTarget"
                    type="number"
                    min="0"
                    max="1000"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    className="col-span-3"
                    placeholder="Enter weekly target (e.g., 50)"
                  />
                </div>

                <p className="text-xs text-muted-foreground text-center">
                  The weekly target will be used to calculate productivity percentage for this employee.
                </p>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTargetDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveTarget} 
              disabled={saveTargetMutation.isPending || loadingWeeklyTarget}
            >
              {saveTargetMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : existingTarget !== undefined && existingTarget !== null ? (
                'Update Target'
              ) : (
                'Save Target'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TeamProductivityPage
