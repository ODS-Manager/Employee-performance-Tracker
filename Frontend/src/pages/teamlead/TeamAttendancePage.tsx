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
import { Calendar, FileText, Loader2, Shield, LogOut, Users } from 'lucide-react'
import odsLogo from '../../assets/ods-logo.png'
import { DailyRosterView } from '../../components/attendance/DailyRosterView'
import { TeamLeadNav } from '../../components/layout/TeamLeadNav'
import { GlobalFilters } from '../../components/filters/GlobalFilters'
import { HeaderRefreshButton } from '../../components/common/HeaderRefreshButton'
import { teamsApi } from '../../services/api'
import { TeamSimple } from '../../types'
import { useAuthStore } from '../../store/authStore'
import { getInitials, handleLogoutFlow } from '../../utils/helpers'

export const TeamAttendancePage: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [teams, setTeams] = useState<TeamSimple[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTeams()
  }, [])

  const loadTeams = async () => {
    setLoading(true)
    try {
      // Get teams where current user is team lead (backend already filters by lead status)
      const response = await teamsApi.myTeams()
      const userTeams = response.items.filter(
        (team) => team.isActive
      )
      setTeams(userTeams)

      // Auto-select first team if only one
      if (userTeams.length === 1) {
        setSelectedTeamId(userTeams[0].id)
      }
    } catch (error) {
      console.error('Failed to load teams:', error)
    } finally {
      setLoading(false)
    }
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
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin text-slate-500 mx-auto mb-3" />
                <p className="text-sm text-slate-600">Loading teams...</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (teams.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50">
        <TeamLeadNav />
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="py-12 text-center">
              <Calendar className="h-12 w-12 mx-auto text-slate-400 mb-4" />
              <h3 className="text-lg font-semibold mb-2 text-slate-900">No Teams Found</h3>
              <p className="text-slate-600 mb-4">
                You are not assigned as a team lead for any active teams.
              </p>
              <Button variant="outline" onClick={() => window.location.reload()}>
                Refresh Page
              </Button>
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
                <h1 className="text-2xl font-bold text-slate-900">Team Attendance</h1>
                <p className="text-sm text-slate-600">
                  {selectedTeam ? selectedTeam.name : teams.length > 1 ? 'Select a team to continue' : 'Mark daily attendance'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Team Filter - Show if multiple teams */}
              {teams.length > 1 && (
                <Select
                  value={selectedTeamId?.toString() || ''}
                  onValueChange={(value) => setSelectedTeamId(parseInt(value))}
                >
                  <SelectTrigger className="w-[220px]">
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
              )}

              {/* Team Badge - Show if single team */}
              {teams.length === 1 && selectedTeam && (
                <Badge variant="outline" className="px-3 py-1">
                  <Users className="w-3 h-3 mr-1" />
                  {selectedTeam.name}
                </Badge>
              )}

              {/* View Reports Button */}
              <Button
                variant="outline"
                onClick={() => navigate('/teamlead/attendance/reports')}
                className="flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                View Reports
              </Button>

              <GlobalFilters showOrgFilter={false} />

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
          {/* Daily Roster */}
          {selectedTeam && (
            <DailyRosterView
              teamId={selectedTeam.id}
              teamName={selectedTeam.name}
            />
          )}

          {/* Select Team Prompt */}
          {!selectedTeamId && teams.length > 1 && (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2 text-slate-900">Select a Team</h3>
                <p className="text-slate-600 max-w-md mx-auto">
                  Please select a team from the dropdown above to start marking attendance.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

export default TeamAttendancePage
