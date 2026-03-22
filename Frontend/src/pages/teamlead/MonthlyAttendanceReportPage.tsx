import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '../../components/ui/dropdown-menu'
import { Download, Users, Loader2, Shield, LogOut, Calendar as CalendarIcon, ChevronLeft, FileText } from 'lucide-react'
import odsLogo from '../../assets/ods-logo.png'
import { TeamLeadNav } from '../../components/layout/TeamLeadNav'
import { HeaderRefreshButton } from '../../components/common/HeaderRefreshButton'
import { attendanceApi, teamsApi } from '../../services/api'
import { TeamSimple, TeamMonthlyAttendanceReport, ExaminerMonthlyAttendance } from '../../types'
import { useAuthStore } from '../../store/authStore'
import { getInitials, handleLogoutFlow } from '../../utils/helpers'
import { format, startOfMonth, endOfMonth, subMonths, getDaysInMonth } from 'date-fns'
import toast from 'react-hot-toast'

interface DayInfo {
  day: number
  dateStr: string
  weekday: string
}

export const MonthlyAttendanceReportPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [teams, setTeams] = useState<TeamSimple[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [selectedMonth, setSelectedMonth] = useState<string>(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [report, setReport] = useState<TeamMonthlyAttendanceReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingReport, setLoadingReport] = useState(false)

  const monthOptions = [
    { value: format(subMonths(new Date(), 2), 'yyyy-MM'), label: format(subMonths(new Date(), 2), 'MMMM yyyy') },
    { value: format(subMonths(new Date(), 1), 'yyyy-MM'), label: format(subMonths(new Date(), 1), 'MMMM yyyy') },
    { value: format(new Date(), 'yyyy-MM'), label: format(new Date(), 'MMMM yyyy') },
  ]

  useEffect(() => {
    loadTeams()
  }, [])

  useEffect(() => {
    if (selectedTeamId && selectedMonth) {
      loadReport()
    }
  }, [selectedTeamId, selectedMonth])

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
    if (!selectedTeamId || !selectedMonth) return
    setLoadingReport(true)
    try {
      const [year, month] = selectedMonth.split('-')
      const startDate = `${selectedMonth}-01`
      const endDate = format(endOfMonth(new Date(parseInt(year), parseInt(month) - 1)), 'yyyy-MM-dd')
      
      const data = await attendanceApi.getTeamMonthlyAttendanceDetail(selectedTeamId, startDate, endDate)
      setReport(data)
    } catch (error: any) {
      console.error('Failed to load monthly report:', error)
      toast.error(error.response?.data?.detail || 'Failed to load monthly attendance report')
    } finally {
      setLoadingReport(false)
    }
  }

  const generateDaysForMonth = (): DayInfo[] => {
    if (!selectedMonth) return []
    const [year, month] = selectedMonth.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1, 1)
    const daysInMonth = getDaysInMonth(date)
    
    const days: DayInfo[] = []
    for (let i = 1; i <= daysInMonth; i++) {
      const dayDate = new Date(parseInt(year), parseInt(month) - 1, i)
      const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      days.push({
        day: i,
        dateStr: format(dayDate, 'yyyy-MM-dd'),
        weekday: weekdays[dayDate.getDay()]
      })
    }
    return days
  }

  const getStatusDisplay = (status: string | null): string => {
    if (status === 'present') return 'P'
    if (status === 'absent') return 'A'
    if (status === 'leave') return 'L'
    return 'N' // Not marked
  }

  const getStatusColor = (status: string | null): string => {
    if (status === 'present') return 'text-green-600 font-bold'
    if (status === 'absent') return 'text-red-600 font-bold'
    if (status === 'leave') return 'text-amber-600 font-bold'
    return 'text-slate-400' // Not marked
  }

  const handleExportCSV = () => {
    if (!report) return

    const days = generateDaysForMonth()
    const headers = ['Employee Name', 'Total Days', 'Present (P)', 'Absent (A)', 'Leave (L)', 'Not Marked (N)', ...days.map(d => String(d.day).padStart(2, '0'))]
    
    const rows = report.examiners.map(emp => {
      const row = [
        emp.userName || 'N/A',
        emp.totalDays,
        emp.daysPresent,
        emp.daysAbsent,
        emp.daysLeave,
        emp.daysNotMarked,
        ...emp.dailyRecords.map(r => getStatusDisplay(r.status))
      ]
      return row
    })

    const csvContent = [
      `Team: ${report.teamName}`,
      `Month: ${selectedMonth}`,
      '',
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `monthly-attendance-${report.teamName}-${selectedMonth}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.success('Monthly report exported successfully')
  }

  const handleLogout = async () => {
    await handleLogoutFlow(logout, navigate)
  }

  const selectedTeam = teams.find((t) => t.id === selectedTeamId)
  const days = generateDaysForMonth()

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

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={odsLogo} alt="ODS Logo" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Monthly Attendance Report</h1>
                <p className="text-sm text-slate-600">
                  {selectedTeam
                    ? selectedTeam.name
                    : teams.length > 1
                    ? 'Select a team to view monthly report'
                    : 'View monthly attendance breakdown'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Back Button */}
              <Button
                variant="outline"
                onClick={() => navigate('/teamlead/attendance')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </Button>

              {/* View Reports Button */}
              <Button
                variant="outline"
                onClick={() => navigate('/teamlead/attendance/reports')}
                className="flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                Summary Report
              </Button>

              {/* Export Button */}
              <Button
                onClick={handleExportCSV}
                disabled={!report || report.examiners.length === 0}
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
              <CardTitle className="text-sm font-medium text-slate-600">Filter Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Team Selection */}
                <div>
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

                {/* Month Selection */}
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-700">Month</label>
                  <Select
                    value={selectedMonth}
                    onValueChange={(value) => setSelectedMonth(value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select month..." />
                    </SelectTrigger>
                    <SelectContent>
                      {monthOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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
                  <p className="text-sm text-slate-600">Loading monthly report...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Legend */}
          {!loadingReport && report && (
            <Card className="bg-slate-50">
              <CardContent className="py-4">
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <span className="font-medium text-slate-700">Legend:</span>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-green-100 text-green-700 font-bold text-xs">P</span>
                    <span className="text-slate-600">Present</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-red-100 text-red-700 font-bold text-xs">A</span>
                    <span className="text-slate-600">Absent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-amber-100 text-amber-700 font-bold text-xs">L</span>
                    <span className="text-slate-600">Leave</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-slate-100 text-slate-500 font-bold text-xs">N</span>
                    <span className="text-slate-600">Not Marked</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Monthly Report Table */}
          {!loadingReport && report && (
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold text-slate-900">
                    {report.teamName} - {format(new Date(parseInt(selectedMonth.split('-')[0]), parseInt(selectedMonth.split('-')[1]) - 1), 'MMMM yyyy')}
                  </CardTitle>
                  <span className="text-sm text-slate-500">
                    {report.examiners.length} Employees
                  </span>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100 sticky top-0">
                      <tr>
                        <th rowSpan={2} className="text-left p-3 font-semibold text-slate-700 border-b border-r min-w-[200px]">
                          Employee Name
                        </th>
                        <th rowSpan={2} className="text-center p-3 font-semibold text-slate-700 border-b border-r min-w-[80px]">
                          Total<br/>Days
                        </th>
                        <th colSpan={4} className="text-center p-2 font-semibold text-slate-700 border-b border-r bg-slate-200">
                          Attendance Summary
                        </th>
                        {days.map((dayInfo) => (
                          <th key={dayInfo.day} className="text-center p-2 font-semibold text-slate-700 border-b min-w-[36px]">
                            <div className="text-xs">{String(dayInfo.day).padStart(2, '0')}</div>
                            <div className="text-[10px] text-slate-500 font-normal">{dayInfo.weekday}</div>
                          </th>
                        ))}
                      </tr>
                      <tr className="bg-slate-50">
                        <th className="text-center p-2 text-xs font-semibold text-green-700 border-b border-r">P</th>
                        <th className="text-center p-2 text-xs font-semibold text-red-700 border-b border-r">A</th>
                        <th className="text-center p-2 text-xs font-semibold text-amber-700 border-b border-r">L</th>
                        <th className="text-center p-2 text-xs font-semibold text-slate-500 border-b border-r">N</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.examiners.map((examiner: ExaminerMonthlyAttendance, index: number) => (
                        <tr
                          key={examiner.userId}
                          className={`border-b hover:bg-slate-50 transition-colors ${
                            index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                          }`}
                        >
                          {/* Employee Name */}
                          <td className="p-3 border-r">
                            <div className="flex items-center gap-3">
                              <div className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center font-medium text-slate-700 text-xs">
                                {getInitials(examiner.userName || '')}
                              </div>
                              <div>
                                <div className="font-medium text-slate-900">{examiner.userName || '-'}</div>
                                {examiner.examinerId && (
                                  <div className="text-xs text-slate-500">ID: {examiner.examinerId}</div>
                                )}
                              </div>
                            </div>
                          </td>

                          {/* Total Days */}
                          <td className="text-center p-3 border-r font-bold text-slate-900">
                            {examiner.totalDays}
                          </td>

                          {/* Present Count */}
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-green-100 text-green-800 font-semibold text-xs">
                              {examiner.daysPresent}
                            </span>
                          </td>

                          {/* Absent Count */}
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-red-100 text-red-800 font-semibold text-xs">
                              {examiner.daysAbsent}
                            </span>
                          </td>

                          {/* Leave Count */}
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-xs">
                              {examiner.daysLeave}
                            </span>
                          </td>

                          {/* Not Marked Count */}
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold text-xs">
                              {examiner.daysNotMarked}
                            </span>
                          </td>

                          {/* Daily Records */}
                          {examiner.dailyRecords.map((record, idx) => (
                            <td key={idx} className="text-center p-2">
                              <span className={getStatusColor(record.status)}>
                                {getStatusDisplay(record.status)}
                              </span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {report.examiners.length === 0 && (
                  <div className="py-12 text-center">
                    <Users className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                    <p className="text-slate-600">No attendance data available for this period</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* No Team Selected */}
          {!selectedTeamId && !loadingReport && (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2 text-slate-900">Select a Team</h3>
                <p className="text-slate-600">
                  Please select a team from the dropdown above to view monthly attendance report.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

export default MonthlyAttendanceReportPage
