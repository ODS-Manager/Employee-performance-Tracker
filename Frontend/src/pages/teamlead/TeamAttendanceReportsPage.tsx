import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Input } from '../../components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '../../components/ui/dropdown-menu'
import { Download, Users, Loader2, Shield, LogOut, Calendar as CalendarIcon, Filter } from 'lucide-react'
import odsLogo from '../../assets/ods-logo.png'
import { TeamLeadNav } from '../../components/layout/TeamLeadNav'
import { HeaderRefreshButton } from '../../components/common/HeaderRefreshButton'
import { attendanceApi, teamsApi } from '../../services/api'
import { TeamSimple, TeamAttendanceReport } from '../../types'
import { useAuthStore } from '../../store/authStore'
import { getInitials, getPacificTodayDate, handleLogoutFlow } from '../../utils/helpers'
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, subWeeks } from 'date-fns'
import toast from 'react-hot-toast'

export const TeamAttendanceReportsPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [teams, setTeams] = useState<TeamSimple[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [report, setReport] = useState<TeamAttendanceReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingReport, setLoadingReport] = useState(false)

  // Date range state — defaults to current week (Mon–Fri)
  const today = getPacificTodayDate()
  const defaultFrom = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd')
  const defaultTo = format(endOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd')
  const [fromDate, setFromDate] = useState<string>(defaultFrom)
  const [toDate, setToDate] = useState<string>(defaultTo)

  useEffect(() => {
    loadTeams()
  }, [])

  useEffect(() => {
    if (selectedTeamId && fromDate && toDate) {
      loadReport()
    }
  }, [selectedTeamId, fromDate, toDate])

  const loadTeams = async () => {
    setLoading(true)
    try {
      const response = await teamsApi.myTeams()
      const userTeams = response.items.filter((team) => team.isActive)
      setTeams(userTeams)
      if (userTeams.length === 1) {
        setSelectedTeamId(userTeams[0].id)
      }
    } catch (error) {
      console.error('Failed to load teams:', error)
      toast.error('Failed to load teams')
    } finally {
      setLoading(false)
    }
  }

  const loadReport = async () => {
    if (!selectedTeamId || !fromDate || !toDate) return
    setLoadingReport(true)
    try {
      const data = await attendanceApi.getTeamAttendanceReport(selectedTeamId, fromDate, toDate)
      setReport(data)
    } catch (error: any) {
      console.error('Failed to load report:', error)
      toast.error(error.response?.data?.detail || 'Failed to load attendance report')
    } finally {
      setLoadingReport(false)
    }
  }

  // Quick date range presets
  const applyCurrentWeek = () => {
    setFromDate(format(startOfWeek(getPacificTodayDate(), { weekStartsOn: 1 }), 'yyyy-MM-dd'))
    setToDate(format(endOfWeek(getPacificTodayDate(), { weekStartsOn: 1 }), 'yyyy-MM-dd'))
  }

  const applyPreviousWeek = () => {
    const prevWeekDay = subWeeks(getPacificTodayDate(), 1)
    setFromDate(format(startOfWeek(prevWeekDay, { weekStartsOn: 1 }), 'yyyy-MM-dd'))
    setToDate(format(endOfWeek(prevWeekDay, { weekStartsOn: 1 }), 'yyyy-MM-dd'))
  }

  const applyCurrentMonth = () => {
    setFromDate(format(startOfMonth(getPacificTodayDate()), 'yyyy-MM-dd'))
    setToDate(format(endOfMonth(getPacificTodayDate()), 'yyyy-MM-dd'))
  }

  const handleExportCSV = () => {
    if (!report) return

    const examiners = report.examiners || []
    const headers = ['Employee Name', 'Working Days', 'Days Present', 'Days Absent', 'Days Leave', 'Attendance %']
    const rows = examiners.map(emp => [
      emp.userName || 'N/A',
      emp.workingDays,
      emp.daysPresent,
      emp.daysAbsent,
      emp.daysLeave,
      emp.attendancePercent.toFixed(2)
    ])

    const csvContent = [
      `Team: ${report.teamName}`,
      `Period: ${fromDate} to ${toDate}`,
      '',
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `attendance-report-${report.teamName}-${fromDate}-to-${toDate}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.success('Report exported successfully')
  }

  const handleLogout = async () => {
    await handleLogoutFlow(logout, navigate)
  }

  const selectedTeam = teams.find((t) => t.id === selectedTeamId)

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <TeamLeadNav />
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const examiners = report?.examiners || []

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={odsLogo} alt="ODS Logo" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Attendance Reports</h1>
                <p className="text-sm text-slate-600">
                  {selectedTeam
                    ? selectedTeam.name
                    : teams.length > 1
                    ? 'Select a team to view reports'
                    : 'View attendance statistics'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Mark Attendance Button */}
              <Button
                variant="outline"
                onClick={() => navigate('/teamlead/attendance')}
                className="flex items-center gap-2"
              >
                <CalendarIcon className="h-4 w-4" />
                Mark Attendance
              </Button>

              {/* Monthly Report Button */}
              <Button
                variant="outline"
                onClick={() => navigate('/teamlead/attendance/monthly-report')}
                className="flex items-center gap-2"
              >
                <CalendarIcon className="h-4 w-4" />
                Monthly Report
              </Button>

              {/* Export Button */}
              <Button
                onClick={handleExportCSV}
                disabled={!report || examiners.length === 0}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export CSV
              </Button>

              <HeaderRefreshButton />

              {/* Team Lead Badge */}
              <Badge variant="outline" className="px-3 py-1">
                <Shield className="w-3 h-3 mr-1" />
                Team Lead
              </Badge>

              {/* User Dropdown */}
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
        <div className="space-y-6">
          {/* Filters */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-slate-500" />
                <CardTitle className="text-sm font-medium text-slate-600">Filter Options</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Team Selection */}
                <div className="lg:col-span-1">
                  <label className="text-sm font-medium mb-2 block text-slate-700">Team</label>
                  <Select
                    value={selectedTeamId?.toString() || ''}
                    onValueChange={(value) => setSelectedTeamId(parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a team..." />
                    </SelectTrigger>
                    <SelectContent>
                      {teams.map((team) => (
                        <SelectItem key={team.id} value={team.id.toString()}>
                          {team.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* From Date */}
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-700">From Date</label>
                  <Input
                    type="date"
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                  />
                </div>

                {/* To Date */}
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-700">To Date</label>
                  <Input
                    type="date"
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                  />
                </div>

                {/* Quick Presets */}
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-700">Quick Select</label>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" onClick={applyCurrentWeek} className="text-xs">
                      This Week
                    </Button>
                    <Button variant="outline" size="sm" onClick={applyPreviousWeek} className="text-xs">
                      Last Week
                    </Button>
                    <Button variant="outline" size="sm" onClick={applyCurrentMonth} className="text-xs">
                      This Month
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Loading State */}
          {loadingReport && (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-500 mx-auto mb-3" />
                  <p className="text-sm text-slate-600">Loading report...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Report Content */}
          {!loadingReport && report && (
            <>
              {/* Summary Cards */}
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      Total Employees
                    </CardTitle>
                    <Users className="h-5 w-5 text-slate-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-slate-900">
                      {report.teamSummary?.examiner_count ?? examiners.length}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">In team</p>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-600">Total Present</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">
                      {report.teamSummary?.total_present ?? 0}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Days marked present</p>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-600">Total Absent</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-red-600">
                      {report.teamSummary?.total_absent ?? 0}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Days unmarked / absent</p>
                  </CardContent>
                </Card>

                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-slate-600">Total Leave</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-amber-600">
                      {report.teamSummary?.total_leave ?? 0}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Days on leave</p>
                  </CardContent>
                </Card>
              </div>

              {/* Employee Attendance Table */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      Employee Attendance Details
                    </CardTitle>
                    <span className="text-xs text-slate-400">
                      {fromDate} — {toDate}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-slate-50">
                          <th className="text-left p-4 font-medium text-sm text-slate-600">Employee</th>
                          <th className="text-center p-4 font-medium text-sm text-slate-600">Working Days</th>
                          <th className="text-center p-4 font-medium text-sm text-slate-600">Present</th>
                          <th className="text-center p-4 font-medium text-sm text-slate-600">Absent</th>
                          <th className="text-center p-4 font-medium text-sm text-slate-600">Leave</th>
                          <th className="text-center p-4 font-medium text-sm text-slate-600">Attendance %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {examiners.map((examiner, index) => (
                          <tr
                            key={examiner.userId ?? index}
                            className={`border-b last:border-b-0 hover:bg-slate-50 transition-colors ${
                              index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                            }`}
                          >
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="h-10 w-10 rounded-full bg-slate-200 flex items-center justify-center font-medium text-slate-700 text-sm">
                                  {examiner.userName?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?'}
                                </div>
                                <div>
                                  <div className="font-medium text-sm text-slate-900">{examiner.userName || '-'}</div>
                                  {examiner.employeeId && (
                                    <div className="text-xs text-slate-500">ID: {examiner.employeeId}</div>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="p-4 text-center font-medium text-slate-900">{examiner.workingDays}</td>
                            <td className="p-4 text-center">
                              <span className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-green-100 text-green-800 font-medium text-sm">
                                {examiner.daysPresent}
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <span className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-red-100 text-red-800 font-medium text-sm">
                                {examiner.daysAbsent}
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <span className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-medium text-sm">
                                {examiner.daysLeave}
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <span className={`text-lg font-bold ${
                                examiner.attendancePercent >= 90
                                  ? 'text-green-600'
                                  : examiner.attendancePercent >= 75
                                  ? 'text-amber-600'
                                  : 'text-red-600'
                              }`}>
                                {examiner.attendancePercent.toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {examiners.length === 0 && (
                    <div className="py-12 text-center">
                      <Users className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                      <p className="text-slate-600">No attendance data available for this period</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {/* No Team Selected */}
          {!selectedTeamId && !loadingReport && (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2 text-slate-900">Select a Team</h3>
                <p className="text-slate-600">
                  Please select a team from the dropdown above to view attendance reports.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

export default TeamAttendanceReportsPage
