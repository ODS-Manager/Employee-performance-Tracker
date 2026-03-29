import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { LoginPage } from './pages/auth/LoginPage'
import { UnauthorizedPage } from './pages/auth/UnauthorizedPage'
import AdminDashboard from './pages/admin/AdminDashboard'
import TeamLeadDashboard from './pages/teamlead/TeamLeadDashboard'
import TeamLeadMembersPage from './pages/teamlead/TeamMembersPage'
import TeamLeadOrdersPage from './pages/teamlead/TeamOrdersPage'
import TeamLeadProductivityPage from './pages/teamlead/TeamProductivityPage'
import TeamLeadTeamManagementPage from './pages/teamlead/TeamLeadTeamManagementPage'
import ExaminerPerformancePage from './pages/teamlead/ExaminerPerformancePage'
import ExaminerDashboard from './pages/examiner/ExaminerDashboard'
import OrderEntryPage from './pages/examiner/OrderEntryPage'
import OrderEditPage from './pages/examiner/OrderEditPage'
import TeamReportsPage from './pages/admin/TeamReportsPage'
import TeamReportDetailPage from './pages/admin/TeamReportDetailPage'
import ExaminerReportsPage from './pages/admin/ExaminerReportsPage'
import ExaminerManagementPage from './pages/admin/ExaminerManagementPage'
import OrderAnalysisPage from './pages/admin/OrderAnalysisPage'
import OnboardingPage from './pages/admin/OnboardingPage'
import TeamManagementPage from './pages/admin/TeamManagementPage'
import ScoreManagementPage from './pages/admin/ScoreManagementPage'
import QualityAuditPage from './pages/admin/QualityAuditPage'
import BillingPage from './pages/admin/BillingPage'
import BillingReportView from './pages/admin/BillingReportView'
import TeamMembersPage from './pages/admin/TeamMembersPage'
import ExaminerDetailPage from './pages/admin/ExaminerDetailPage'
import ExaminerPerformanceDetailPage from './pages/admin/ExaminerPerformanceDetailPage'
import OrganizationsPage from './pages/admin/OrganizationsPage'
import ReferenceDataPage from './pages/admin/ReferenceDataPage'
import ProductivityReportsPage from './pages/admin/ProductivityReportsPage'
import ExaminerTargetsPage from './pages/admin/ExaminerTargetsPage'
import TeamLeadTargetsPage from './pages/admin/TeamLeadTargetsPage'
import AdminTeamLeadAttendancePage from './pages/admin/AdminTeamLeadAttendancePage'
import AdminMonthlyAttendanceReportPage from './pages/admin/AdminMonthlyAttendanceReportPage'
import TeamAttendancePage from './pages/teamlead/TeamAttendancePage'
import TeamAttendanceReportsPage from './pages/teamlead/TeamAttendanceReportsPage'
import MonthlyAttendanceReportPage from './pages/teamlead/MonthlyAttendanceReportPage'
import TeamLeadPersonalDashboard from './pages/teamlead/TeamLeadPersonalDashboard'
import './App.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
      retry: 1,
      staleTime: 10 * 60 * 1000, // 10 minutes - data stays fresh longer
      gcTime: 30 * 60 * 1000, // 30 minutes - keep data in cache longer (formerly cacheTime)
    },
  },
})

// Component to handle smart default routing based on authentication status
const DefaultRoute = () => {
  const { user, isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }
  
  // Redirect to appropriate dashboard based on user role
  const userRole = user.userRole?.toLowerCase()
  if (userRole === 'superadmin' || userRole === 'admin') {
    return <Navigate to="/admin/dashboard" replace />
  } else if (userRole === 'team_lead') {
    return <Navigate to="/teamlead/dashboard" replace />
  } else {
    return <Navigate to="/examiner/dashboard" replace />
  }
}

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth)

  // Check authentication status on app load
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Admin Routes */}
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/teams"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <TeamReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/team-report/:id"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <TeamReportDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/examiners"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ExaminerReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/examiner-management"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ExaminerManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/orders"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <OrderAnalysisPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/onboarding"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/team-management"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <TeamManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/score-management"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ScoreManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/quality-audit"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin', 'team_lead']}>
                  <QualityAuditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/billing"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <BillingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/billing/:id"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <BillingReportView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/teams/:teamId/members"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <TeamMembersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/examiners/:userId"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ExaminerDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/examiners/:userId/performance"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ExaminerPerformanceDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/organizations"
              element={
                <ProtectedRoute requiredRoles={['superadmin']}>
                  <OrganizationsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/reference-data"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ReferenceDataPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/productivity"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <ProductivityReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/examiner-targets"
              element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <ExaminerTargetsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/attendance/team-leads"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <AdminTeamLeadAttendancePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/attendance/monthly-report"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <AdminMonthlyAttendanceReportPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/team-lead-targets"
              element={
                <ProtectedRoute requiredRoles={['admin', 'superadmin']}>
                  <TeamLeadTargetsPage />
                </ProtectedRoute>
              }
            />

            {/* Team Lead Routes */}
            <Route
              path="/teamlead/dashboard"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/team"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadMembersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/orders"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadOrdersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/productivity"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadProductivityPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/team-management"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadTeamManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/teams/:teamId/members"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamMembersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/teams/:teamId/targets"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <ExaminerTargetsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/teamlead/examiner/:userId/performance"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <ExaminerPerformancePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/quality-audit"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <QualityAuditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/attendance"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamAttendancePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/attendance/reports"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamAttendanceReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/attendance/monthly-report"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <MonthlyAttendanceReportPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teamlead/personal-dashboard"
              element={
                <ProtectedRoute requiredRoles={['team_lead']}>
                  <TeamLeadPersonalDashboard />
                </ProtectedRoute>
              }
            />

{/* Examiner Routes */}
            <Route
              path="/examiner/dashboard"
              element={
                <ProtectedRoute requiredRoles={['examiner']}>
                  <ExaminerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/examiner/new-order"
              element={
                <ProtectedRoute requiredRoles={['examiner', 'team_lead', 'admin', 'superadmin']}>
                  <OrderEntryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/examiner/edit-order/:orderId"
              element={
                <ProtectedRoute requiredRoles={['examiner', 'team_lead', 'admin', 'superadmin']}>
                  <OrderEditPage />
                </ProtectedRoute>
              }
            />

            {/* Smart Default Route - redirects based on authentication status */}
            <Route path="/" element={<DefaultRoute />} />
            
            {/* 404 Route - redirects to smart default */}
            <Route path="*" element={<DefaultRoute />} />
          </Routes>
        </div>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 5000,
            error: {
              duration: 8000,
              style: {
                background: '#ef4444',
                color: '#fff',
              },
            },
            success: {
              duration: 3000,
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
