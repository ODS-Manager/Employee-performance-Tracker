import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { usersApi, teamsApi, organizationsApi } from '../../services/api'
import type { Organization, Team, UserRole } from '../../types'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { Alert, AlertDescription } from '../../components/ui/alert'
import { UserPlus, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

export const OnboardingPage = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  
  const [formData, setFormData] = useState({
    userName: '',
    employeeId: '',
    password: '',
    confirmPassword: '',
    userRole: 'examiner' as UserRole,
    orgId: user?.orgId || null as number | null,
  })
  
  const [teams, setTeams] = useState<Team[]>([])
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [selectedTeams, setSelectedTeams] = useState<number[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [teamAssignmentErrors, setTeamAssignmentErrors] = useState<string[]>([])

  useEffect(() => {
    if (!user || !['admin', 'superadmin'].includes(user.userRole)) {
      navigate('/login')
      return
    }
    fetchInitialData()
  }, [user, navigate])

  // Fetch teams when organization changes (for admin users who don't use the selector)
  useEffect(() => {
    if (formData.orgId && user?.userRole !== 'superadmin') {
      fetchTeamsForOrg(formData.orgId)
    } else if (!formData.orgId) {
      setTeams([])
      setSelectedTeams([])
    }
  }, [formData.orgId, user?.userRole])

  const fetchInitialData = async () => {
    try {
      setError('') // Clear previous errors
      
      // Superadmin can see all organizations
      if (user?.userRole === 'superadmin') {
        const orgsRes = await organizationsApi.list({ isActive: true })
        setOrganizations(orgsRes.items || [])
        
        if (!orgsRes.items || orgsRes.items.length === 0) {
          setError('No organizations found. Please create an organization first.')
        }
      } else if (user?.orgId) {
        // Admin - fetch teams for their org
        await fetchTeamsForOrg(user.orgId)
      } else {
        setError('Unable to determine your organization. Please contact support.')
      }
    } catch (error: any) {
      console.error('Failed to fetch data:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to load initial data. Please refresh the page.'
      setError(errorMsg)
      toast.error(errorMsg)
    }
  }

  const fetchTeamsForOrg = async (orgId: number) => {
    try {
      setLoadingTeams(true)
      setError('') // Clear previous errors
      const teamsRes = await teamsApi.list({ 
        orgId: orgId,
        isActive: true 
      })
      setTeams(teamsRes.items || [])
      
      // Show message if no teams found
      if (!teamsRes.items || teamsRes.items.length === 0) {
        toast.info('No teams available for this organization. Please create teams first.')
      }
    } catch (error: any) {
      console.error('Failed to fetch teams:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to load teams. Please try again.'
      setError(errorMsg)
      toast.error(errorMsg)
      setTeams([])
    } finally {
      setLoadingTeams(false)
    }
  }

  const handleOrgChange = async (value: string) => {
    try {
      const orgId = parseInt(value)
      setFormData({...formData, orgId})
      setError('') // Clear errors when org changes
      setTeams([]) // Reset teams when org changes
      setSelectedTeams([]) // Clear selected teams
      
      // Fetch teams for the selected organization
      if (orgId) {
        await fetchTeamsForOrg(orgId)
      }
    } catch (error: any) {
      console.error('Failed to change organization:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to load teams for selected organization'
      setError(errorMsg)
      toast.error(errorMsg)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)
    setTeamAssignmentErrors([])

    // Validation
    if (!formData.userName || !formData.employeeId || !formData.password) {
      setError('Please fill in all required fields')
      return
    }

    // Validate Employee ID format
    const employeeIdRegex = /^[A-Z0-9_-]+$/i
    if (!employeeIdRegex.test(formData.employeeId)) {
      setError('Employee ID can only contain letters, numbers, hyphens, and underscores')
      return
    }
    if (formData.employeeId.length < 2) {
      setError('Employee ID must be at least 2 characters')
      return
    }
    if (formData.employeeId.length > 50) {
      setError('Employee ID must be at most 50 characters')
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    // Non-superadmin users must have an organization
    if (formData.userRole !== 'superadmin' && !formData.orgId) {
      setError('Please select a center')
      return
    }

    setIsLoading(true)
    let newUser: any = null
    const failedTeams: string[] = []

    try {
      // Step 1: Create the user with manual Employee ID
      newUser = await usersApi.create({
        userName: formData.userName,
        employeeId: formData.employeeId.trim().toUpperCase(),
        password: formData.password,
        userRole: formData.userRole,
        orgId: formData.userRole === 'superadmin' ? null : formData.orgId,
      })

      // Step 2: Add user to selected teams (don't fail if team assignment fails)
      if (selectedTeams.length > 0 && newUser?.id) {
        for (const teamId of selectedTeams) {
          try {
            await usersApi.addToTeam(newUser.id, { 
              userId: newUser.id, 
              teamId,
              role: 'member'
            })
          } catch (teamError: any) {
            console.error(`Failed to add user to team ${teamId}:`, teamError)
            const teamName = teams.find(t => t.id === teamId)?.name || `Team ID ${teamId}`
            const errorDetail = teamError.response?.data?.detail || 'Unknown error'
            failedTeams.push(`${teamName}: ${errorDetail}`)
          }
        }
      }

      // Update state with team assignment errors
      setTeamAssignmentErrors(failedTeams)
      setSuccess(true)
      
      // Show appropriate success message
      if (failedTeams.length > 0) {
        // Partial success - user created but some teams failed
        toast.success(`Employee "${formData.userName}" created successfully!`)
        toast.error(`Failed to assign to ${failedTeams.length} team(s). You can assign teams later from Team Management.`, {
          duration: 5000
        })
      } else {
        toast.success('Employee created successfully!')
      }
      
      // Reset form
      setFormData({
        userName: '',
        employeeId: '',
        password: '',
        confirmPassword: '',
        userRole: 'examiner',
        orgId: user?.orgId || null,
      })
      setSelectedTeams([])
      
    } catch (error: any) {
      let errorMsg = 'Failed to create employee'
      const detail = error.response?.data?.detail
      const status = error.response?.status
      
      if (status === 401) {
        errorMsg = 'Your session has expired. Please log in again.'
      } else if (status === 403) {
        errorMsg = 'You do not have permission to create employees.'
      } else if (detail) {
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          // Handle Pydantic validation errors (422)
          errorMsg = detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
        } else if (typeof detail === 'object') {
          errorMsg = detail.msg || detail.message || JSON.stringify(detail)
        }
      } else if (error.message) {
        errorMsg = error.message
      }
      
      setError(errorMsg)
      toast.error(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTeamToggle = (teamId: number) => {
    setSelectedTeams(prev => 
      prev.includes(teamId) 
        ? prev.filter(id => id !== teamId)
        : [...prev, teamId]
    )
  }

  // Determine if we should show organization selector
  const showOrgSelector = user?.userRole === 'superadmin' && formData.userRole !== 'superadmin'
  
  // Get the effective orgId for team display
  const effectiveOrgId = formData.orgId

  return (
    <div className="min-h-screen bg-slate-50">
      <Toaster position="top-right" />
      
      <AdminHeader title="Employee Onboarding" subtitle="Add new employees and team leads" />
      
      <AdminNav />
      
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              New Employee
            </CardTitle>
            <CardDescription>Fill in the details to onboard a new team member</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mb-6 border-green-200 bg-green-50">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Employee created successfully!
                  <span className="block mt-1 text-sm">You can add another employee or navigate away.</span>
                </AlertDescription>
              </Alert>
            )}

            {/* Show partial success warning if user created but teams failed */}
            {success && teamAssignmentErrors.length > 0 && (
              <Alert className="mb-6 border-amber-200 bg-amber-50">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  <strong>Note:</strong> Employee was created but could not be assigned to all selected teams:
                  <ul className="list-disc list-inside mt-2 text-sm">
                    {teamAssignmentErrors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                  <p className="mt-2 text-sm">You can assign teams later from the Team Management section.</p>
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Role & Center - Move this up so teams can be filtered */}
              <div className="space-y-4">
                <h3 className="font-medium text-sm text-slate-700">Role & Center</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="role">Role *</Label>
                    <Select 
                      value={formData.userRole} 
                      onValueChange={(value: UserRole) => setFormData({...formData, userRole: value})}
                      disabled={isLoading}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="examiner">Employee</SelectItem>
                        <SelectItem value="team_lead">Team Lead</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                        {user?.userRole === 'superadmin' && (
                          <SelectItem value="superadmin">Super Admin</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Center selector (for superadmin only) */}
                  {showOrgSelector && (
                    <div className="space-y-2">
                      <Label htmlFor="organization">Organization *</Label>
                      <Select 
                        value={formData.orgId ? formData.orgId.toString() : undefined} 
                        onValueChange={handleOrgChange}
                        disabled={isLoading}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select center" />
                        </SelectTrigger>
                        <SelectContent>
                          {organizations.map((org) => (
                            <SelectItem key={org.id} value={org.id.toString()}>
                              {org.name} ({org.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </div>

              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="font-medium text-sm text-slate-700">Basic Information</h3>
                
                <div className="space-y-2">
                  <Label htmlFor="userName">Username *</Label>
                  <Input 
                    id="userName" 
                    placeholder="e.g., John Doe"
                    value={formData.userName} 
                    onChange={(e) => {
                      const val = e.target.value;
                      // Allow only letters, numbers, spaces, dots, hyphens
                      if (val === '' || /^[a-zA-Z][a-zA-Z0-9 .\-]*$/.test(val) || /^[a-zA-Z]$/.test(val)) {
                        setFormData({...formData, userName: val});
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value.trim();
                      if (val.length > 0) {
                        setFormData({...formData, userName: val.charAt(0).toUpperCase() + val.slice(1)});
                      }
                    }}
                    required 
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground">
                    Must start with a letter. Allows letters, numbers, spaces, dots, and hyphens. Min 2 characters.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employeeId">Employee ID *</Label>
                  <Input 
                    id="employeeId" 
                    placeholder="e.g., EMP001 or JD-2024-001"
                    value={formData.employeeId} 
                    onChange={(e) => {
                      const val = e.target.value;
                      // Allow letters, numbers, hyphens, and underscores
                      if (val === '' || /^[a-zA-Z0-9_-]*$/.test(val)) {
                        setFormData({...formData, employeeId: val});
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value.trim().toUpperCase();
                      setFormData({...formData, employeeId: val});
                    }}
                    required 
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground">
                    Required. Unique identifier for the employee. Use letters, numbers, hyphens, or underscores. Will be converted to uppercase.
                  </p>
                </div>
              </div>

              {/* Password */}
              <div className="space-y-4">
                <h3 className="font-medium text-sm text-slate-700">Password</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="password">Password *</Label>
                    <Input 
                      id="password" 
                      type="password" 
                      placeholder="Min 8 characters"
                      value={formData.password} 
                      onChange={(e) => setFormData({...formData, password: e.target.value})} 
                      required 
                      disabled={isLoading}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm Password *</Label>
                    <Input 
                      id="confirmPassword" 
                      type="password" 
                      placeholder="Re-enter password"
                      value={formData.confirmPassword} 
                      onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})} 
                      required 
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>

              {/* Team Assignment - Only show if org is selected and role is not superadmin */}
              {formData.userRole !== 'superadmin' && effectiveOrgId && (
                <div className="space-y-4">
                  <h3 className="font-medium text-sm text-slate-700">Team Assignment (Optional)</h3>
                  
                  {loadingTeams ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading teams...
                    </div>
                  ) : teams.length > 0 ? (
                    <>
                      <p className="text-xs text-muted-foreground">Select teams to assign this employee to</p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {teams.map((team) => (
                          <Button
                            key={team.id}
                            type="button"
                            variant={selectedTeams.includes(team.id) ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTeamToggle(team.id)}
                            disabled={isLoading}
                            className="justify-start"
                          >
                            {team.name}
                          </Button>
                        ))}
                      </div>
                      
                      {selectedTeams.length > 0 && (
                        <p className="text-xs text-muted-foreground">
                          Selected: {selectedTeams.length} team(s)
                        </p>
                      )}
                    </>
                  ) : (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-md">
                      <p className="text-sm text-amber-800">
                        <AlertCircle className="h-4 w-4 inline mr-2" />
                        No teams available for this organization.
                      </p>
                      <p className="text-xs text-amber-600 mt-1">
                        Please create teams in the Team Management section first.
                      </p>
                      <Button 
                        type="button" 
                        variant="outline" 
                        size="sm" 
                        className="mt-3"
                        onClick={() => fetchTeamsForOrg(effectiveOrgId!)}
                        disabled={loadingTeams}
                      >
                        {loadingTeams ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <AlertCircle className="h-4 w-4 mr-2" />
                        )}
                        Retry Loading Teams
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Show message if superadmin needs to select org first */}
              {showOrgSelector && !formData.orgId && formData.userRole !== 'superadmin' && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <p className="text-sm text-blue-800">
                    <AlertCircle className="h-4 w-4 inline mr-2" />
                    Please select an organization above to view available teams.
                  </p>
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Employee...
                  </>
                ) : (
                  <>
                    <UserPlus className="mr-2 h-4 w-4" />
                    Create Employee
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default OnboardingPage
