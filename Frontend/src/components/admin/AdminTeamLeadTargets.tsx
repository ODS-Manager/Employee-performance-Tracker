import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { weeklyTargetsApi } from '../../services/api'
import { formatStoredDate, getPacificWeekStartDate } from '../../utils/helpers'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Badge } from '../../components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table'
import {
  Users,
  Save, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  CheckCircle,
  AlertCircle,
  UserCog
} from 'lucide-react'
import toast from 'react-hot-toast'

interface TeamLeadTarget {
  userId: number
  userName: string
  employeeId: string
  currentTarget: number | null
  previousTarget: number | null
  targetId: number | null
}

interface TargetEditState {
  [userId: number]: string
}

export const AdminTeamLeadTargets = () => {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  
  const [weekOffset, setWeekOffset] = useState(0)
  const [targetEdits, setTargetEdits] = useState<TargetEditState>({})
  const [hasChanges, setHasChanges] = useState(false)

  // Calculate week dates based on offset
  const getWeekDates = (offset: number) => getPacificWeekStartDate(offset)

  const weekStartDate = getWeekDates(weekOffset)

  // Fetch team lead targets
  const { data: targetsData, isLoading: loadingTargets } = useQuery({
    queryKey: ['team-lead-targets', weekStartDate],
    queryFn: () => weeklyTargetsApi.getTeamLeadTargets(weekStartDate),
    enabled: !!user,
  })

  const teamLeads: TeamLeadTarget[] = targetsData?.members || []
  const weekInfo = targetsData?.weekInfo

  // Reset edits when data changes
  useEffect(() => {
    setTargetEdits({})
    setHasChanges(false)
  }, [targetsData])

  const handleTargetChange = (userId: number, value: string) => {
    setTargetEdits(prev => ({
      ...prev,
      [userId]: value
    }))
    setHasChanges(true)
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const membersToUpdate = Object.entries(targetEdits)
        .filter(([_, value]) => value.trim() !== '')
        .map(([userId, value]) => ({
          userId: parseInt(userId),
          target: parseInt(value) || 0
        }))

      if (membersToUpdate.length === 0) {
        throw new Error('No targets to save')
      }

      return weeklyTargetsApi.setTeamLeadTargets({
        weekStartDate: weekStartDate,
        members: membersToUpdate
      })
    },
    onSuccess: () => {
      toast.success('Team lead targets saved successfully')
      queryClient.invalidateQueries({ queryKey: ['team-lead-targets'] })
      setHasChanges(false)
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || error.message || 'Failed to save targets'
      toast.error(msg)
    }
  })

  const handleSave = () => {
    saveMutation.mutate()
  }

  const navigateWeek = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setWeekOffset(prev => prev - 1)
    } else {
      setWeekOffset(prev => prev + 1)
    }
  }

  const getWeekLabel = () => {
    if (weekOffset === 0) return 'Current Week'
    if (weekOffset === -1) return 'Previous Week'
    if (weekOffset === 1) return 'Next Week'
    if (weekOffset < -1) return `${Math.abs(weekOffset)} Weeks Ago`
    return `${weekOffset} Weeks From Now`
  }

  const canEdit = weekInfo?.canEdit ?? true

  return (
    <div className="space-y-6">
      {/* Week Navigation */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              Weekly Targets
            </CardTitle>
            <CardDescription>
              Set targets for team leads ({getWeekLabel()})
            </CardDescription>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigateWeek('prev')}
              disabled={weekOffset <= -4}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="text-center min-w-[150px]">
              <p className="font-medium">
                {weekInfo?.weekStartDate ? formatStoredDate(weekInfo.weekStartDate) : weekStartDate}
              </p>
              <p className="text-xs text-muted-foreground">to</p>
              <p className="font-medium">
                {weekInfo?.weekEndDate ? formatStoredDate(weekInfo.weekEndDate) : ''}
              </p>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigateWeek('next')}
              disabled={weekOffset >= 4}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        {weekInfo?.isPastWeek && (
          <CardContent>
            <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-yellow-600" />
              <p className="text-sm text-yellow-800">
                This is a past week.
              </p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Team Leads Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Team Leads
            </CardTitle>
            <CardDescription>
              {teamLeads.length} team leads
            </CardDescription>
          </div>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || !canEdit || saveMutation.isPending}
            className="flex items-center gap-2"
          >
            {saveMutation.isPending ? (
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
        </CardHeader>
        <CardContent>
          {loadingTargets ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : teamLeads.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <UserCog className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No team leads found</p>
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Team Lead</TableHead>
                    <TableHead>Employee ID</TableHead>
                    <TableHead>Previous Target</TableHead>
                    <TableHead>Current Target</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {teamLeads.map((teamLead) => {
                    const editValue = targetEdits[teamLead.userId]
                    const displayValue = editValue !== undefined ? editValue : (teamLead.currentTarget?.toString() || '')
                    const hasTarget = teamLead.currentTarget !== null && teamLead.currentTarget > 0

                    return (
                      <TableRow key={teamLead.userId}>
                        <TableCell className="font-medium">
                          {teamLead.userName}
                        </TableCell>
                        <TableCell>
                          {teamLead.employeeId}
                        </TableCell>
                        <TableCell>
                          {teamLead.previousTarget !== null && teamLead.previousTarget > 0 ? (
                            <Badge variant="outline">{teamLead.previousTarget}</Badge>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            value={displayValue}
                            onChange={(e) => handleTargetChange(teamLead.userId, e.target.value)}
                            disabled={!canEdit}
                            className="w-24"
                            placeholder="0"
                          />
                        </TableCell>
                        <TableCell>
                          {hasTarget ? (
                            <Badge className="bg-green-500">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Set
                            </Badge>
                          ) : (
                            <Badge variant="secondary">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Not Set
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default AdminTeamLeadTargets
