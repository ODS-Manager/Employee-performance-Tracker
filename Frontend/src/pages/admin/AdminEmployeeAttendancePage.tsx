import { useEffect, useState } from 'react'
import { CalendarDays, Loader2, Users } from 'lucide-react'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { AdminNav } from '../../components/layout/AdminNav'
import { DailyRosterView } from '../../components/attendance/DailyRosterView'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { teamsApi } from '../../services/api'
import { TeamSimple } from '../../types'
import toast from 'react-hot-toast'

/**
 * Admins can manage employee attendance for every active team they are allowed
 * to access. The shared roster component keeps editing behaviour identical to
 * the team-lead portal while the API enforces organization boundaries.
 */
export const AdminEmployeeAttendancePage = () => {
  const [teams, setTeams] = useState<TeamSimple[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTeams = async () => {
      setLoading(true)
      try {
        const response = await teamsApi.list({ isActive: true, pageSize: 1000 })
        const activeTeams = response.items.filter((team) => team.isActive)
        setTeams(activeTeams)
        if (activeTeams.length > 0) {
          setSelectedTeamId(activeTeams[0].id)
        }
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to load teams')
      } finally {
        setLoading(false)
      }
    }

    loadTeams()
  }, [])

  const selectedTeam = teams.find((team) => team.id === selectedTeamId)

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Employee Attendance" subtitle="View and manage attendance for all employees" />
      <AdminNav />

      <main className="container mx-auto px-4 py-8 space-y-6">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Employee Attendance
                </CardTitle>
                <CardDescription>
                  Select a team, then choose a date in the roster to mark or correct attendance.
                </CardDescription>
              </div>

              <Select
                value={selectedTeamId?.toString() || ''}
                onValueChange={(value) => setSelectedTeamId(Number(value))}
                disabled={loading || teams.length === 0}
              >
                <SelectTrigger className="w-full md:w-[280px]">
                  <SelectValue placeholder="Select a team" />
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
          </CardHeader>
        </Card>

        {loading ? (
          <Card>
            <CardContent className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
            </CardContent>
          </Card>
        ) : !selectedTeam ? (
          <Card>
            <CardContent className="py-12 text-center text-slate-600">
              <CalendarDays className="mx-auto mb-3 h-12 w-12 text-slate-400" />
              No active teams are available for attendance management.
            </CardContent>
          </Card>
        ) : (
          <DailyRosterView key={selectedTeam.id} teamId={selectedTeam.id} teamName={selectedTeam.name} />
        )}
      </main>
    </div>
  )
}

export default AdminEmployeeAttendancePage
