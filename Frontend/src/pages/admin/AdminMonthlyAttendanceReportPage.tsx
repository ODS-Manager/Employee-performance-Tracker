import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Download, Users, Loader2 } from 'lucide-react'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { AdminNav } from '../../components/layout/AdminNav'
import { api } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { getInitials } from '../../utils/helpers'
import { format, startOfMonth, endOfMonth, subMonths, getDaysInMonth } from 'date-fns'
import toast from 'react-hot-toast'

interface DayInfo {
  day: number
  dateStr: string
  weekday: string
}

interface TeamLeadMonthlyAttendance {
  userId: number
  userName: string
  employeeId: string
  totalDays: number
  daysPresent: number
  daysAbsent: number
  daysLeave: number
  daysNotMarked: number
  dailyRecords: { date: string; status: string | null }[]
}

interface TeamLeadsMonthlyReport {
  teamId: number
  teamName: string
  startDate: string
  endDate: string
  examiners: TeamLeadMonthlyAttendance[]
}

export const AdminMonthlyAttendanceReportPage = () => {
  const { user } = useAuthStore()
  const [selectedMonth, setSelectedMonth] = useState<string>(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [report, setReport] = useState<TeamLeadsMonthlyReport | null>(null)
  const [loadingReport, setLoadingReport] = useState(false)

  const monthOptions = [
    { value: format(subMonths(new Date(), 2), 'yyyy-MM'), label: format(subMonths(new Date(), 2), 'MMMM yyyy') },
    { value: format(subMonths(new Date(), 1), 'yyyy-MM'), label: format(subMonths(new Date(), 1), 'MMMM yyyy') },
    { value: format(new Date(), 'yyyy-MM'), label: format(new Date(), 'MMMM yyyy') },
  ]

  useEffect(() => {
    if (selectedMonth) {
      loadReport()
    }
  }, [selectedMonth])

  const loadReport = async () => {
    if (!selectedMonth) return
    setLoadingReport(true)
    try {
      const [year, month] = selectedMonth.split('-')
      const startDate = `${selectedMonth}-01`
      const endDate = format(endOfMonth(new Date(parseInt(year), parseInt(month) - 1)), 'yyyy-MM-dd')

      const response = await api.get('/attendance/team-leads/monthly', {
        params: { start_date: startDate, end_date: endDate }
      })
      setReport(response.data)
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
    return 'N'
  }

  const getStatusColor = (status: string | null): string => {
    if (status === 'present') return 'text-green-600 font-bold'
    if (status === 'absent') return 'text-red-600 font-bold'
    if (status === 'leave') return 'text-amber-600 font-bold'
    return 'text-slate-400'
  }

  const handleExportCSV = () => {
    if (!report) return

    const days = generateDaysForMonth()
    const headers = ['Team Lead Name', 'Employee ID', 'Total Days', 'Present (P)', 'Absent (A)', 'Leave (L)', 'Not Marked (N)', ...days.map(d => String(d.day).padStart(2, '0'))]

    const rows = report.examiners.map((emp: TeamLeadMonthlyAttendance) => {
      const row = [
        emp.userName || 'N/A',
        emp.employeeId || 'N/A',
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
      `All Team Leads - Monthly Attendance Report`,
      `Month: ${selectedMonth}`,
      '',
      headers.join(','),
      ...rows.map((row: any[]) => row.join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `team-leads-monthly-attendance-${selectedMonth}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    toast.success('Monthly report exported successfully')
  }

  const days = generateDaysForMonth()

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Team Lead Monthly Attendance" subtitle="View monthly attendance for all team leads" />
      <AdminNav />

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Filters */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600">Filter Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-700">Month</label>
                  <Select value={selectedMonth} onValueChange={(value) => setSelectedMonth(value)}>
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

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button onClick={handleExportCSV} disabled={!report || report.examiners.length === 0}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>

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
                    Team Leads - {format(new Date(parseInt(selectedMonth.split('-')[0]), parseInt(selectedMonth.split('-')[1]) - 1), 'MMMM yyyy')}
                  </CardTitle>
                  <span className="text-sm text-slate-500">{report.examiners.length} Team Leads</span>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100 sticky top-0">
                      <tr>
                        <th rowSpan={2} className="text-left p-3 font-semibold text-slate-700 border-b border-r min-w-[200px]">Team Lead</th>
                        <th rowSpan={2} className="text-center p-3 font-semibold text-slate-700 border-b border-r min-w-[80px]">Total<br/>Days</th>
                        <th colSpan={4} className="text-center p-2 font-semibold text-slate-700 border-b border-r bg-slate-200">Attendance Summary</th>
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
                      {report.examiners.map((examiner: TeamLeadMonthlyAttendance, index: number) => (
                        <tr key={examiner.userId} className={`border-b hover:bg-slate-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                          <td className="p-3 border-r">
                            <div className="flex items-center gap-3">
                              <Avatar>
                                <AvatarFallback className="bg-slate-200 text-slate-700 text-xs">{getInitials(examiner.userName || '')}</AvatarFallback>
                              </Avatar>
                              <div>
                                <div className="font-medium text-slate-900">{examiner.userName || '-'}</div>
                                {examiner.employeeId && <div className="text-xs text-slate-500">ID: {examiner.employeeId}</div>}
                              </div>
                            </div>
                          </td>
                          <td className="text-center p-3 border-r font-bold text-slate-900">{examiner.totalDays}</td>
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-green-100 text-green-800 font-semibold text-xs">{examiner.daysPresent}</span>
                          </td>
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-red-100 text-red-800 font-semibold text-xs">{examiner.daysAbsent}</span>
                          </td>
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-xs">{examiner.daysLeave}</span>
                          </td>
                          <td className="text-center p-2 border-r">
                            <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold text-xs">{examiner.daysNotMarked}</span>
                          </td>
                          {examiner.dailyRecords.map((record, idx) => (
                            <td key={idx} className="text-center p-2">
                              <span className={getStatusColor(record.status)}>{getStatusDisplay(record.status)}</span>
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
                    <p className="text-slate-600">No team leads found for this period</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* No Data */}
          {!loadingReport && !report && (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2 text-slate-900">Select a Month</h3>
                <p className="text-slate-600">Please select a month to view the attendance report.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

export default AdminMonthlyAttendanceReportPage