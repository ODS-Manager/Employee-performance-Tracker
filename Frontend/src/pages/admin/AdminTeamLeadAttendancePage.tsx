import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { attendanceApi, teamsApi, usersApi } from '../../services/api'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Calendar } from '../../components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover'
import { format } from 'date-fns'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { AdminNav } from '../../components/layout/AdminNav'
import { formatStoredDate, getInitials, getPacificTodayDate } from '../../utils/helpers'
import toast from 'react-hot-toast'
import { 
  Calendar as CalendarIcon, 
  Users, 
  CheckCircle2, 
  XCircle, 
  Clock,
  Loader2,
  Save,
  CalendarDays,
  UserCog
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface TeamLead {
  id: number
  userName: string
  employeeId: string
  isActive: boolean
}

interface AttendanceRecord {
  userId: number
  date: string
  status: 'present' | 'absent' | 'leave' | null
  notes?: string
}

export const AdminTeamLeadAttendancePage = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState<Date>(getPacificTodayDate())
  const [attendanceRecords, setAttendanceRecords] = useState<Record<number, AttendanceRecord>>({})
  const [saving, setSaving] = useState(false)

  // Redirect if not admin or superadmin
  useEffect(() => {
    if (!user || (user.userRole !== 'admin' && user.userRole !== 'superadmin')) {
      navigate('/login')
    }
  }, [user, navigate])

  // Fetch all team leads
  const { data: teamLeadsData, isLoading: loadingTeamLeads } = useQuery({
    queryKey: ['users', 'team-leads', user?.orgId],
    queryFn: () => usersApi.list({ 
      role: 'team_lead', 
      isActive: true,
      pageSize: 1000 
    }),
    enabled: !!user && (user.userRole === 'admin' || user.userRole === 'superadmin'),
  })

  const teamLeads = teamLeadsData?.items || []

  // Fetch existing attendance for selected date
  const { data: existingAttendance, isLoading: loadingAttendance } = useQuery({
    queryKey: ['attendance', 'team-leads', format(selectedDate, 'yyyy-MM-dd')],
    queryFn: async () => {
      // Get attendance for all team leads for the selected date
      const records: Record<number, any> = {}
      await Promise.all(
        teamLeads.map(async (tl: TeamLead) => {
          try {
            const summary = await attendanceApi.getTeamLeadAttendance(
              tl.id,
              format(selectedDate, 'yyyy-MM-dd'),
              format(selectedDate, 'yyyy-MM-dd')
            )
            if (summary && summary.records && summary.records.length > 0) {
              records[tl.id] = {
                userId: tl.id,
                date: format(selectedDate, 'yyyy-MM-dd'),
                status: summary.records[0].status,
                notes: summary.records[0].notes
              }
            }
          } catch (error) {
            // No attendance record found, which is fine
          }
        })
      )
      return records
    },
    enabled: teamLeads.length > 0 && !!selectedDate,
    staleTime: 5 * 60 * 1000,
  })

  // Initialize attendance records from existing data
  useEffect(() => {
    if (existingAttendance) {
      setAttendanceRecords(existingAttendance)
    }
  }, [existingAttendance])

  const handleStatusChange = (teamLeadId: number, status: 'present' | 'absent' | 'leave') => {
    setAttendanceRecords(prev => ({
      ...prev,
      [teamLeadId]: {
        userId: teamLeadId,
        date: format(selectedDate, 'yyyy-MM-dd'),
        status,
        notes: prev[teamLeadId]?.notes || ''
      }
    }))
  }

  const handleNotesChange = (teamLeadId: number, notes: string) => {
    setAttendanceRecords(prev => ({
      ...prev,
      [teamLeadId]: {
        ...prev[teamLeadId],
        userId: teamLeadId,
        date: format(selectedDate, 'yyyy-MM-dd'),
        notes
      }
    }))
  }

  const handleSaveAttendance = async () => {
    setSaving(true)
    try {
      const recordsToSave = Object.values(attendanceRecords).filter(r => r.status !== null)
      
      for (const record of recordsToSave) {
        await attendanceApi.markTeamLeadAttendance({
          userId: record.userId,
          teamId: 0, // Team leads don't belong to a specific team for attendance
          date: record.date,
          status: record.status as 'present' | 'absent' | 'leave',
          notes: record.notes
        })
      }

      toast.success('Attendance saved successfully')
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
    } catch (error: any) {
      const msg = error.response?.data?.detail || 'Failed to save attendance'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  const getStatusBadge = (status: string | null) => {
    switch (status) {
      case 'present':
        return <Badge className="bg-green-500">Present</Badge>
      case 'absent':
        return <Badge className="bg-red-500">Absent</Badge>
      case 'leave':
        return <Badge className="bg-yellow-500">Leave</Badge>
      default:
        return <Badge variant="outline">Not Marked</Badge>
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Team Lead Attendance" subtitle="Mark attendance for team leads" />
      <AdminNav />

      <main className="container mx-auto px-4 py-8">
        <Card className="mb-6">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <UserCog className="h-5 w-5" />
                  Team Lead Attendance
                </CardTitle>
                <CardDescription>
                  Select a date and mark attendance for team leads
                </CardDescription>
              </div>

              <div className="flex items-center gap-4">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[240px] justify-start text-left font-normal",
                        !selectedDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                    {selectedDate ? formatStoredDate(selectedDate.toISOString().slice(0, 10), 'en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="end">
                    <Calendar
                      mode="single"
                      selected={selectedDate}
                      onSelect={(date) => date && setSelectedDate(date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Team Leads</CardTitle>
              <CardDescription>
                {formatStoredDate(selectedDate.toISOString().slice(0, 10), 'en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })} - {teamLeads.length} team leads
              </CardDescription>
            </div>
            <Button 
              onClick={handleSaveAttendance} 
              disabled={saving || Object.keys(attendanceRecords).length === 0}
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
                  Save Attendance
                </>
              )}
            </Button>
          </CardHeader>
          <CardContent>
            {loadingTeamLeads ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              </div>
            ) : teamLeads.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <UserCog className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No team leads found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {teamLeads.map((teamLead: TeamLead) => {
                  const record = attendanceRecords[teamLead.id]
                  const currentStatus = record?.status || null

                  return (
                    <div 
                      key={teamLead.id} 
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <Avatar>
                          <AvatarFallback className="bg-primary text-primary-foreground">
                            {getInitials(teamLead.userName)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{teamLead.userName}</p>
                          <p className="text-sm text-muted-foreground">ID: {teamLead.employeeId}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {getStatusBadge(currentStatus)}
                        
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant={currentStatus === 'present' ? 'default' : 'outline'}
                            onClick={() => handleStatusChange(teamLead.id, 'present')}
                            className={currentStatus === 'present' ? 'bg-green-600 hover:bg-green-700' : ''}
                          >
                            <CheckCircle2 className="h-4 w-4 mr-1" />
                            Present
                          </Button>
                          <Button
                            size="sm"
                            variant={currentStatus === 'absent' ? 'default' : 'outline'}
                            onClick={() => handleStatusChange(teamLead.id, 'absent')}
                            className={currentStatus === 'absent' ? 'bg-red-600 hover:bg-red-700' : ''}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            Absent
                          </Button>
                          <Button
                            size="sm"
                            variant={currentStatus === 'leave' ? 'default' : 'outline'}
                            onClick={() => handleStatusChange(teamLead.id, 'leave')}
                            className={currentStatus === 'leave' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
                          >
                            <Clock className="h-4 w-4 mr-1" />
                            Leave
                          </Button>
                        </div>

                        <input
                          type="text"
                          placeholder="Notes (optional)"
                          value={record?.notes || ''}
                          onChange={(e) => handleNotesChange(teamLead.id, e.target.value)}
                          className="px-3 py-1 border rounded-md text-sm w-48 focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default AdminTeamLeadAttendancePage
