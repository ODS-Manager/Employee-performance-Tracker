import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Textarea } from '../ui/textarea'
import { Badge } from '../ui/badge'
import { ChevronLeft, ChevronRight, Save, UserCheck, Loader2, Calendar as CalendarIcon, CheckCircle2, Clock, Coffee } from 'lucide-react'
import { attendanceApi } from '../../services/api'
import { AttendanceStatus, DailyRosterExaminer, DailyRosterResponse } from '../../types'
import { format, addDays, subDays } from 'date-fns'
import { formatStoredDate, getPacificTodayDate, parseStoredDateToUtcDate } from '../../utils/helpers'
import toast from 'react-hot-toast'

interface DailyRosterViewProps {
  teamId: number
  teamName: string
  onDateChange?: (date: Date) => void
}

interface EmployeeAttendanceState {
  userId: number
  status: AttendanceStatus | 'not_marked'
  notes: string
  attendanceId?: number
}

const attendanceStateChanged = (
  current: EmployeeAttendanceState,
  original?: EmployeeAttendanceState
) => {
  if (!original) return current.status !== 'not_marked' || Boolean(current.notes)
  return current.status !== original.status || current.notes !== original.notes
}

export const DailyRosterView: React.FC<DailyRosterViewProps> = ({
  teamId,
  teamName,
  onDateChange,
}) => {
  const [selectedDate, setSelectedDate] = useState<Date>(getPacificTodayDate())
  const [roster, setRoster] = useState<DailyRosterResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [attendanceStates, setAttendanceStates] = useState<Record<number, EmployeeAttendanceState>>({})
  const [savedAttendanceStates, setSavedAttendanceStates] = useState<Record<number, EmployeeAttendanceState>>({})

  // Load roster data
  useEffect(() => {
    loadRoster()
  }, [teamId, selectedDate])

  const loadRoster = async () => {
    setLoading(true)
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd')
      const data = await attendanceApi.getDailyRoster(teamId, dateStr)
      const examiners = data.examiners || []
      setRoster({ ...data, examiners })

      // Initialize attendance states from roster
      const states: Record<number, EmployeeAttendanceState> = {}
      examiners.forEach((emp) => {
        states[emp.userId] = {
          userId: emp.userId,
          status: emp.status === 'present' || emp.status === 'half_day' || emp.status === 'leave'
            ? emp.status
            : 'not_marked',
          notes: emp.notes || '',
          attendanceId: emp.attendanceId,
        }
      })
      setAttendanceStates(states)
      setSavedAttendanceStates(states)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load roster')
    } finally {
      setLoading(false)
    }
  }

  const handlePrevDay = () => {
    const prevDay = subDays(selectedDate, 1)
    setSelectedDate(prevDay)
    onDateChange?.(prevDay)
  }

  const handleNextDay = () => {
    const nextDay = addDays(selectedDate, 1)
    if (nextDay <= getPacificTodayDate()) {
      setSelectedDate(nextDay)
      onDateChange?.(nextDay)
    }
  }

  const handleDateSelection = (value: string) => {
    if (!value) return
    const nextDate = parseStoredDateToUtcDate(value)
    if (!nextDate || nextDate > getPacificTodayDate()) return
    setSelectedDate(nextDate)
    onDateChange?.(nextDate)
  }

  const updateEmployeeStatus = (userId: number, status: AttendanceStatus | 'not_marked') => {
    setAttendanceStates((prev) => ({
      ...prev,
      [userId]: {
        ...prev[userId],
        status,
      },
    }))
  }

  const updateEmployeeNotes = (userId: number, notes: string) => {
    setAttendanceStates((prev) => ({
      ...prev,
      [userId]: {
        ...prev[userId],
        notes,
      },
    }))
  }

  const handleMarkAllPresent = () => {
    setAttendanceStates((previous) => Object.fromEntries(
      Object.entries(previous).map(([userId, state]) => [
        userId,
        { ...state, status: AttendanceStatus.PRESENT },
      ])
    ))
  }

  const handleMarkAllHalfDay = () => {
    setAttendanceStates((previous) => Object.fromEntries(
      Object.entries(previous).map(([userId, state]) => [
        userId,
        { ...state, status: AttendanceStatus.HALF_DAY },
      ])
    ))
  }

  const handleClearAll = () => {
    setAttendanceStates((previous) => Object.fromEntries(
      Object.entries(previous).map(([userId, state]) => [
        userId,
        { ...state, status: 'not_marked', notes: '' },
      ])
    ))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd')

      const changedStates = Object.values(attendanceStates).filter((state) =>
        attendanceStateChanged(state, savedAttendanceStates[state.userId])
      )

      if (changedStates.length === 0) {
        toast.success('No attendance changes to save')
        return
      }

      const promises = changedStates.map(async (state) => {
        if (state.status === 'not_marked') {
          if (state.attendanceId) {
            await attendanceApi.unmarkAttendance(state.attendanceId)
          }
          return
        }

        if (state.attendanceId) {
          await attendanceApi.updateAttendance(state.attendanceId, {
            status: state.status as AttendanceStatus,
            notes: state.notes || undefined,
          })
          return
        }

        await attendanceApi.markAttendance({
          userId: state.userId,
          teamId,
          date: dateStr,
          status: state.status as AttendanceStatus,
          notes: state.notes || undefined,
        })
      })

      await Promise.all(promises)

      toast.success('Attendance changes saved successfully')

      // Reload roster to get updated data
      await loadRoster()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save attendance')
    } finally {
      setSaving(false)
    }
  }

  const canNavigatePrev = true
  const canNavigateNext = addDays(selectedDate, 1) <= getPacificTodayDate()

  const getStatusBadge = (status: AttendanceStatus | 'not_marked') => {
    switch (status) {
      case AttendanceStatus.PRESENT:
        return (
          <Badge className="bg-green-100 text-green-800 border-green-200 hover:bg-green-100">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Present
          </Badge>
        )
      case AttendanceStatus.HALF_DAY:
        return (
          <Badge className="bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-100">
            <Clock className="h-3 w-3 mr-1" />
            Half Day
          </Badge>
        )
      case AttendanceStatus.LEAVE:
        return (
          <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-100">
            <Coffee className="h-3 w-3 mr-1" />
            Leave
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="text-gray-500">
            Not Marked
          </Badge>
        )
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-slate-500 mx-auto mb-3" />
            <p className="text-sm text-slate-600">Loading roster...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Card with Date Navigation */}
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <CardTitle className="text-sm font-medium text-slate-600">
              Daily Attendance - {teamName}
            </CardTitle>
            
            {/* Date Navigation */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrevDay}
                disabled={!canNavigatePrev}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="min-w-[180px] text-center">
                <div className="font-medium text-sm text-slate-900">
                  {formatStoredDate(selectedDate.toISOString().slice(0, 10), 'en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                </div>
                <label className="sr-only" htmlFor={`attendance-date-${teamId}`}>Attendance date</label>
                <div className="mt-1 flex items-center justify-center gap-1 text-slate-500">
                  <CalendarIcon className="h-3.5 w-3.5" />
                  <input
                    id={`attendance-date-${teamId}`}
                    type="date"
                    value={selectedDate.toISOString().slice(0, 10)}
                    max={getPacificTodayDate().toISOString().slice(0, 10)}
                    onChange={(event) => handleDateSelection(event.target.value)}
                    className="bg-transparent text-xs outline-none"
                  />
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleNextDay}
                disabled={!canNavigateNext}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        {/* Statistics Bar */}
        {roster && (
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-600 font-medium">Present</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{roster.summary.present}</p>
              </div>
              
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-600 font-medium">Half Day</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{roster.summary.half_day}</p>
              </div>
              
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-600 font-medium">Leave</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{roster.summary.leave}</p>
              </div>
              
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-600 font-medium">Not Marked</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{roster.summary.not_marked}</p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap gap-2 pb-4 border-b">
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAllPresent}
                className="flex items-center gap-2"
              >
                <UserCheck className="h-4 w-4" />
                Mark All Present
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAllHalfDay}
                className="flex items-center gap-2"
              >
                <Clock className="h-4 w-4" />
                Mark All Half Day
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearAll}
              >
                Clear All
              </Button>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Employee Attendance Table */}
      {roster && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="text-left p-4 font-medium text-sm text-slate-600">Employee</th>
                    <th className="text-left p-4 font-medium text-sm text-slate-600">Status</th>
                    <th className="text-left p-4 font-medium text-sm text-slate-600">Quick Actions</th>
                    <th className="text-left p-4 font-medium text-sm text-slate-600">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {roster.examiners.map((employee, index) => (
                    <tr
                      key={employee.userId}
                      className={`border-b last:border-b-0 hover:bg-slate-50 transition-colors ${
                        index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                      }`}
                    >
                      {/* Employee Info */}
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-slate-200 flex items-center justify-center font-medium text-slate-700 text-sm">
                            {employee.userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-sm text-slate-900">{employee.userName}</div>
                            <div className="text-xs text-slate-500">
                              ID: {employee.employeeId}
                            </div>
                            {employee.markedByName && (
                              <div className="text-xs text-slate-500 mt-1">
                                Marked by {employee.markedByName}
                              </div>
                            )}
                            {employee.modifiedByName && (
                              <div className="text-xs text-slate-500 mt-1">
                                Last updated by {employee.modifiedByName}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Status Dropdown */}
                      <td className="p-4">
                        <Select
                          value={attendanceStates[employee.userId]?.status || 'not_marked'}
                          onValueChange={(value) =>
                            updateEmployeeStatus(
                              employee.userId,
                              value as AttendanceStatus | 'not_marked'
                            )
                          }
                        >
                          <SelectTrigger className="w-[150px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="not_marked">Not Marked</SelectItem>
                            <SelectItem value={AttendanceStatus.PRESENT}>Present</SelectItem>
                            <SelectItem value={AttendanceStatus.HALF_DAY}>Half Day</SelectItem>
                            <SelectItem value={AttendanceStatus.LEAVE}>Leave</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>

                      {/* Quick Action Buttons */}
                      <td className="p-4">
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => updateEmployeeStatus(employee.userId, AttendanceStatus.PRESENT)}
                            className="h-8 w-8 p-0"
                            title="Mark Present"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => updateEmployeeStatus(employee.userId, AttendanceStatus.HALF_DAY)}
                            className="h-8 w-8 p-0"
                            title="Mark Half Day"
                          >
                            <Clock className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => updateEmployeeStatus(employee.userId, AttendanceStatus.LEAVE)}
                            className="h-8 w-8 p-0"
                            title="Mark Leave"
                          >
                            <Coffee className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>

                      {/* Notes */}
                      <td className="p-4">
                        <Textarea
                          placeholder="Add notes..."
                          value={attendanceStates[employee.userId]?.notes || ''}
                          onChange={(e) =>
                            updateEmployeeNotes(employee.userId, e.target.value)
                          }
                          rows={1}
                          className="text-sm min-w-[200px] resize-none"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Save Button Footer */}
            <div className="border-t bg-slate-50 p-4 flex justify-between items-center">
              <p className="text-sm text-slate-600">
                {roster.examiners.length} employee{roster.examiners.length !== 1 ? 's' : ''} in roster
              </p>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
