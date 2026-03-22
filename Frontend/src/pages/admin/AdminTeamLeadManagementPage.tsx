import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { hasAnyUserRole } from '../../utils/helpers'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { AdminNav } from '../../components/layout/AdminNav'
import { 
  UserCog, 
  CalendarDays, 
  Target,
  ArrowLeft
} from 'lucide-react'
import AdminTeamLeadAttendance from '../../components/admin/AdminTeamLeadAttendance'
import AdminTeamLeadTargets from '../../components/admin/AdminTeamLeadTargets'

export const AdminTeamLeadManagementPage = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('attendance')

  // Only allow admin and superadmin
  if (!user || !hasAnyUserRole(user.userRole, ['admin', 'superadmin'])) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              You don't have permission to access this page.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/admin/dashboard')} className="w-full">
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader 
        title="Team Lead Management" 
        subtitle="Manage team lead attendance and targets" 
      />
      <AdminNav />

      <main className="container mx-auto px-4 py-6">
        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <UserCog className="h-6 w-6" />
                Team Lead Management
              </CardTitle>
              <CardDescription>
                Manage attendance and productivity targets for team leads
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={() => navigate('/admin/dashboard')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
          </CardHeader>
        </Card>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="attendance" className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4" />
              Attendance
            </TabsTrigger>
            <TabsTrigger value="targets" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Targets
            </TabsTrigger>
          </TabsList>

          <TabsContent value="attendance" className="space-y-4">
            <AdminTeamLeadAttendance />
          </TabsContent>

          <TabsContent value="targets" className="space-y-4">
            <AdminTeamLeadTargets />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default AdminTeamLeadManagementPage
