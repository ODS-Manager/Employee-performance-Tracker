import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore } from '../../store/dashboardFilterStore'
import { billingApi, organizationsApi, teamsApi } from '../../services/api'
import type { BillingReport, BillingPreviewResponse, Organization, Team } from '../../types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Label } from '../../components/ui/label'
import { Input } from '../../components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../components/ui/dialog'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import {
  FileText,
  Plus,
  RefreshCw,
  Loader2,
  Eye,
  CheckCircle2,
  XCircle,
  Trash2,
  AlertCircle,
  Calendar,
  FileCheck,
  Download
} from 'lucide-react'
import toast from 'react-hot-toast'

export const BillingPage = () => {
  const { user } = useAuthStore()
  const { filterOrgId, setFilterOrgId } = useDashboardFilterStore()
  const navigate = useNavigate()

  const [reports, setReports] = useState<BillingReport[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [preview, setPreview] = useState<BillingPreviewResponse | null>(null)
  const [showFinalizeDialog, setShowFinalizeDialog] = useState(false)
  const [reportToFinalize, setReportToFinalize] = useState<BillingReport | null>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [reportToDelete, setReportToDelete] = useState<BillingReport | null>(null)

  // Centers state (for superadmin)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)

  // Use global filter for organization
  const selectedOrgId = user?.userRole === 'superadmin'
    ? (filterOrgId ? parseInt(filterOrgId) : undefined)
    : undefined
  
  // Fetch teams for team selection filter
  const { data: teamsData } = useQuery({
    queryKey: ['teams', 'billing', selectedOrgId],
    queryFn: () => teamsApi.list({ 
      orgId: selectedOrgId,
      isActive: true
    }),
    enabled: !!selectedOrgId || user?.userRole !== 'superadmin',
  })
  const teams = teamsData?.items || []

  // Local filters for the reports list view - now using dates
  const [listFilterStartDate, setListFilterStartDate] = useState<string>('')
  const [listFilterEndDate, setListFilterEndDate] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)

  // Form state for creating new billing reports - now using dates
  const [formStartDate, setFormStartDate] = useState<string>(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  )
  const [formEndDate, setFormEndDate] = useState<string>(
    new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0]
  )

  useEffect(() => {
    if (!user || !['admin', 'superadmin'].includes(user.userRole)) {
      navigate('/login')
    } else {
      fetchInitialData()
    }
  }, [user, navigate])

  useEffect(() => {
    if (user) {
      fetchReports()
    }
  }, [listFilterStartDate, listFilterEndDate, filterStatus, selectedOrgId])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      // Fetch organizations if superadmin
      if (user?.userRole === 'superadmin') {
        const orgsRes = await organizationsApi.list({ isActive: true })
        setOrganizations(orgsRes.items || [])
        // Note: We no longer set a default org - it's controlled by global filter
      }
      const params: any = {}
      if (selectedOrgId) params.orgId = selectedOrgId
      const reportsRes = await billingApi.list(params)
      setReports(reportsRes.items || [])
    } catch (error) {
      console.error('Failed to fetch initial data:', error)
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const fetchReports = async () => {
    try {
      const params: any = {}
      if (listFilterStartDate) params.startDate = listFilterStartDate
      if (listFilterEndDate) params.endDate = listFilterEndDate
      if (filterStatus) params.status = filterStatus
      if (selectedOrgId) params.orgId = selectedOrgId

      const response = await billingApi.list(params)
      setReports(response.items || [])
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    }
  }

  const handlePreview = async () => {
    if (!formStartDate || !formEndDate) {
      toast.error('Please select start and end dates')
      return
    }

    if (new Date(formStartDate) > new Date(formEndDate)) {
      toast.error('Start date must be before end date')
      return
    }

    // Check if superadmin and no org selected
    if (user?.userRole === 'superadmin' && !selectedOrgId) {
      toast.error('Please select a center')
      return
    }

    try {
      setProcessing(true)
      const previewData = await billingApi.preview({
        startDate: formStartDate,
        endDate: formEndDate,
        orgId: user?.userRole === 'superadmin' ? selectedOrgId : undefined,
        teamId: selectedTeamId || undefined,
      })

      if (previewData.totalFiles === 0) {
        toast.error('No pending orders found for this period')
        return
      }

      setPreview(previewData)
      setShowPreview(true)
    } catch (error: any) {
      console.error('Failed to preview billing data:', error)
      toast.error(error.response?.data?.detail || 'Failed to preview billing data')
    } finally {
      setProcessing(false)
    }
  }

  const handleCreate = async () => {
    if (!formStartDate || !formEndDate) {
      toast.error('Please select start and end dates')
      return
    }

    if (new Date(formStartDate) > new Date(formEndDate)) {
      toast.error('Start date must be before end date')
      return
    }

    // Check if superadmin and no org selected
    if (user?.userRole === 'superadmin' && !selectedOrgId) {
      toast.error('Please select a center')
      return
    }

    try {
      setProcessing(true)
      await billingApi.create({
        startDate: formStartDate,
        endDate: formEndDate,
        orgId: user?.userRole === 'superadmin' ? selectedOrgId : undefined,
        teamId: selectedTeamId || undefined,
      })

      toast.success('Billing report created successfully')
      setShowCreateForm(false)
      setShowPreview(false)
      setPreview(null)
      resetForm()
      fetchReports()
    } catch (error: any) {
      console.error('Failed to create billing report:', error)
      toast.error(error.response?.data?.detail || 'Failed to create billing report')
    } finally {
      setProcessing(false)
    }
  }

  const handleFinalize = (report: BillingReport) => {
    setReportToFinalize(report)
    setShowFinalizeDialog(true)
  }

  const confirmFinalize = async () => {
    if (!reportToFinalize) return

    try {
      setProcessing(true)
      await billingApi.finalize(reportToFinalize.id)
      toast.success('Billing report finalized successfully')
      setShowFinalizeDialog(false)
      setReportToFinalize(null)
      fetchReports()
    } catch (error: any) {
      console.error('Failed to finalize billing report:', error)
      toast.error(error.response?.data?.detail || 'Failed to finalize billing report')
    } finally {
      setProcessing(false)
    }
  }

  const handleDelete = (report: BillingReport) => {
    if (report.status === 'finalized') {
      toast.error('Cannot delete finalized billing reports')
      return
    }
    setReportToDelete(report)
    setShowDeleteDialog(true)
  }

  const confirmDelete = async () => {
    if (!reportToDelete) return

    try {
      await billingApi.delete(reportToDelete.id)
      toast.success('Billing report deleted successfully')
      setShowDeleteDialog(false)
      setReportToDelete(null)
      fetchReports()
    } catch (error: any) {
      console.error('Failed to delete billing report:', error)
      toast.error(error.response?.data?.detail || 'Failed to delete billing report')
    }
  }

  const handleViewDetails = (report: BillingReport) => {
    navigate(`/admin/billing/${report.id}`)
  }

  const handleExportExcel = async (report: BillingReport) => {
    try {
      toast.loading('Generating Excel file...', { id: 'export-excel' })
      await billingApi.exportExcel(report.id)
      toast.success('Excel file downloaded successfully', { id: 'export-excel' })
    } catch (error: any) {
      console.error('Failed to export billing report:', error)
      toast.error(error.response?.data?.detail || 'Failed to export billing report', { id: 'export-excel' })
    }
  }

  const resetForm = () => {
    setFormStartDate(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0])
    setFormEndDate(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0])
  }

  const getStatusBadge = (status: string) => {
    if (status === 'finalized') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded">
          <CheckCircle2 className="h-3 w-3" />
          Finalized
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold text-yellow-700 bg-yellow-100 rounded">
        <AlertCircle className="h-3 w-3" />
        Draft
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader 
        title="Billing Reports" 
        subtitle="Center-wide monthly billing grouped by product types" 
      />
      <AdminNav />

      <main className="container mx-auto px-4 py-8">
        {/* Page Actions */}
        <div className="flex items-center justify-end mb-6">
          <Button
            onClick={() => {
              resetForm()
              setShowCreateForm(!showCreateForm)
              setShowPreview(false)
            }}
          >
            {showCreateForm ? (
              <>
                <XCircle className="h-4 w-4 mr-2" />
                Cancel
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                New Billing Report
              </>
            )}
          </Button>
        </div>

        {/* Create Form */}
        {showCreateForm && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>New Billing Report</CardTitle>
              <CardDescription>
                Select billing period to generate center-wide report
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Center selector for superadmin */}
                {user?.userRole === 'superadmin' && (
                  <div className="space-y-2">
                    <Label>Organization *</Label>
                    <Select
                      value={selectedOrgId?.toString() || ''}
                      onValueChange={(value) => {
                        setFilterOrgId(value)
                        setSelectedTeamId(null)
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select center" />
                      </SelectTrigger>
                      <SelectContent>
                        {organizations.map((org) => (
                          <SelectItem key={org.id} value={org.id.toString()}>
                            {org.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Team selector for filtering by specific team */}
                {teams.length > 0 && (
                  <div className="space-y-2">
                    <Label>Team (Optional)</Label>
                    <Select
                      value={selectedTeamId?.toString() || 'all'}
                      onValueChange={(value) => setSelectedTeamId(value === 'all' ? null : parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All Teams" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Teams</SelectItem>
                        {teams.map((team) => (
                          <SelectItem key={team.id} value={team.id.toString()}>
                            {team.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Start Date *</Label>
                    <Input
                      type="date"
                      value={formStartDate}
                      onChange={(e) => setFormStartDate(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>End Date *</Label>
                    <Input
                      type="date"
                      value={formEndDate}
                      onChange={(e) => setFormEndDate(e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button onClick={handlePreview} disabled={processing} variant="outline">
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <Eye className="h-4 w-4 mr-2" />
                        Preview Data
                      </>
                    )}
                  </Button>

                  {showPreview && preview && (
                    <Button onClick={handleCreate} disabled={processing}>
                      {processing ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <FileCheck className="h-4 w-4 mr-2" />
                          Create Report
                        </>
                      )}
                    </Button>
                  )}
                </div>

                {/* Preview Table */}
                {showPreview && preview && (() => {
                   // Group preview details by team
                   const teamOrder = [
                    'Florida', 'California', 'GI Clearing', 'Washington', 'Michigan',
                    'Colorado', 'Utah', 'Oregon', 'Regional Streamline', 'National Streamline',
                    'FIF', 'SCB & PD', 'Arizona', 'Texas', 'Pennsylvania', 'Ohio', 'Guam',
                    'Georgia', 'Vietnam Team'
                  ]

                  const teamData: Record<string, Array<{
                    product: string
                    directSingleSeat: number
                    directStep1: number
                    directStep2: number
                    agencySingleSeat: number
                    agencyStep1: number
                    agencyStep2: number
                  }>> = {}

                   preview.details.forEach((detail) => {
                    // Use teamName directly from API response
                    const teamName = detail.teamName
                    const productName = detail.productName

                    if (!teamData[teamName]) {
                      teamData[teamName] = []
                    }

                    // Find or create product entry
                    let productEntry = teamData[teamName].find(p => p.product === productName)
                    if (!productEntry) {
                      productEntry = {
                        product: productName,
                        directSingleSeat: 0,
                        directStep1: 0,
                        directStep2: 0,
                        agencySingleSeat: 0,
                        agencyStep1: 0,
                        agencyStep2: 0,
                      }
                      teamData[teamName].push(productEntry)
                    }

                    // Populate counts based on division
                    if (detail.divisionName === 'Direct') {
                      productEntry.directSingleSeat = detail.singleSeatCount
                      productEntry.directStep1 = detail.onlyStep1Count
                      productEntry.directStep2 = detail.onlyStep2Count
                    } else if (detail.divisionName === 'Agency') {
                      productEntry.agencySingleSeat = detail.singleSeatCount
                      productEntry.agencyStep1 = detail.onlyStep1Count
                      productEntry.agencyStep2 = detail.onlyStep2Count
                    }
                  })

                  const sortedTeams = Object.keys(teamData).sort((a, b) => {
                    const aIdx = teamOrder.indexOf(a)
                    const bIdx = teamOrder.indexOf(b)
                    return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx)
                  })

                  sortedTeams.forEach(team => {
                    teamData[team].sort((a, b) => a.product.localeCompare(b.product))
                  })

                  // Calculate grand totals
                  let grandTotalSingleSeat = 0
                  let grandTotalStep1 = 0
                  let grandTotalStep2 = 0
                  sortedTeams.forEach(team => {
                    teamData[team].forEach(p => {
                      grandTotalSingleSeat += p.directSingleSeat + p.agencySingleSeat
                      grandTotalStep1 += p.directStep1 + p.agencyStep1
                      grandTotalStep2 += p.directStep2 + p.agencyStep2
                    })
                  })

                  return (
                    <div className="mt-6">
                      <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
                        <h3 className="font-semibold text-blue-900 mb-2">Preview Summary</h3>
                         <div className="grid md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-blue-700">Period:</span>{' '}
                            <span className="font-medium">
                              {new Date(preview.startDate).toLocaleDateString()} - {new Date(preview.endDate).toLocaleDateString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-blue-700">Total Files:</span>{' '}
                            <span className="font-medium">{preview.totalFiles}</span>
                          </div>
                          <div>
                            <span className="text-blue-700">Teams:</span>{' '}
                            <span className="font-medium">{preview.teamsCount}</span>
                          </div>
                        </div>
                      </div>

                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Team Name</TableHead>
                            <TableHead>Product Type</TableHead>
                            <TableHead>Division</TableHead>
                            <TableHead>Process Type</TableHead>
                            <TableHead className="text-center">Count</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {sortedTeams.map((teamName) => {
                            const products = teamData[teamName]
                            let teamRowRendered = false

                            return products.map((product) => {
                              const subRows = [
                                { division: 'Direct', label: 'Single Seat', count: product.directSingleSeat || 0 },
                                { division: 'Direct', label: 'Step 1', count: product.directStep1 || 0 },
                                { division: 'Direct', label: 'Step 2', count: product.directStep2 || 0 },
                                { division: 'Agency', label: 'Single Seat', count: product.agencySingleSeat || 0 },
                                { division: 'Agency', label: 'Step 1', count: product.agencyStep1 || 0 },
                                { division: 'Agency', label: 'Step 2', count: product.agencyStep2 || 0 },
                              ]

                              return subRows.map((sub, subIdx) => {
                                const showTeamName = !teamRowRendered
                                const showProductName = subIdx === 0
                                if (showTeamName) teamRowRendered = true

                                return (
                                  <TableRow
                                    key={`${teamName}-${product.product}-${sub.division}-${sub.label}`}
                                    className={subIdx === 5 ? 'border-b-2 border-slate-200' : ''}
                                  >
                                    <TableCell className={showTeamName ? 'font-medium' : ''}>
                                      {showTeamName ? teamName : ''}
                                    </TableCell>
                                    <TableCell className={showProductName ? 'font-medium' : ''}>
                                      {showProductName ? product.product : ''}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground">
                                      {sub.division}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground">
                                      {sub.label}
                                    </TableCell>
                                    <TableCell className="text-center font-semibold">
                                      {sub.count}
                                    </TableCell>
                                  </TableRow>
                                )
                              })
                            })
                          })}
                          <TableRow className="bg-slate-100 font-semibold border-t-2">
                            <TableCell>GRAND TOTAL</TableCell>
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell className="text-sm">Single Seat</TableCell>
                            <TableCell className="text-center">{grandTotalSingleSeat}</TableCell>
                          </TableRow>
                          <TableRow className="bg-slate-100 font-semibold">
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell className="text-sm">Step 1</TableCell>
                            <TableCell className="text-center">{grandTotalStep1}</TableCell>
                          </TableRow>
                          <TableRow className="bg-slate-100 font-semibold">
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell className="text-sm">Step 2</TableCell>
                            <TableCell className="text-center">{grandTotalStep2}</TableCell>
                          </TableRow>
                          <TableRow className="bg-slate-50 font-bold border-t-2">
                            <TableCell>TOTAL</TableCell>
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell></TableCell>
                            <TableCell className="text-center">{preview.totalFiles}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                  )
                })()}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="flex items-center gap-4 flex-wrap">
              <Label className="whitespace-nowrap">Filter by:</Label>

              <div className="space-y-2">
                <Input
                  type="date"
                  value={listFilterStartDate}
                  onChange={(e) => setListFilterStartDate(e.target.value)}
                  placeholder="Start Date"
                  className="w-40"
                />
              </div>

              <div className="space-y-2">
                <Input
                  type="date"
                  value={listFilterEndDate}
                  onChange={(e) => setListFilterEndDate(e.target.value)}
                  placeholder="End Date"
                  className="w-40"
                />
              </div>

              <Select
                value={filterStatus || 'all'}
                onValueChange={(value) => setFilterStatus(value === 'all' ? null : value)}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="finalized">Finalized</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm" onClick={fetchReports}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Reports List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Billing Reports
            </CardTitle>
            <CardDescription>View and manage monthly billing reports</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : reports.length > 0 ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Period</TableHead>
                      <TableHead className="text-center">Total Files</TableHead>
                      <TableHead className="text-center">Status</TableHead>
                      <TableHead>Created By</TableHead>
                      <TableHead>Finalized By</TableHead>
                      <TableHead className="text-center">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-slate-500" />
                            {new Date(report.startDate).toLocaleDateString()} - {new Date(report.endDate).toLocaleDateString()}
                          </div>
                        </TableCell>
                        <TableCell className="text-center font-semibold">
                          {report.totalFiles}
                        </TableCell>
                        <TableCell className="text-center">{getStatusBadge(report.status)}</TableCell>
                        <TableCell className="text-sm">
                          {report.createdByName}
                          <div className="text-xs text-muted-foreground">
                            {new Date(report.createdAt).toLocaleDateString()}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {report.finalizedByName ? (
                            <>
                              {report.finalizedByName}
                              <div className="text-xs text-muted-foreground">
                                {report.finalizedAt
                                  ? new Date(report.finalizedAt).toLocaleDateString()
                                  : ''}
                              </div>
                            </>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetails(report)}
                              title="View Details"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleExportExcel(report)}
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              title="Export to Excel"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                            {report.status === 'draft' && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleFinalize(report)}
                                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                  title="Finalize Report"
                                >
                                  <CheckCircle2 className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(report)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  title="Delete Report"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-30" />
                <p>No billing reports found</p>
                <p className="text-sm mt-1">Click "New Billing Report" to create your first report</p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Finalize Confirmation Dialog */}
      <Dialog open={showFinalizeDialog} onOpenChange={setShowFinalizeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Finalize Billing Report</DialogTitle>
            <DialogDescription>
              Are you sure you want to finalize this billing report? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {reportToFinalize && (
            <div className="bg-slate-50 p-4 rounded-md">
              <p className="text-sm">
                <span className="font-medium">Period:</span>{' '}
                {new Date(reportToFinalize.startDate).toLocaleDateString()} - {new Date(reportToFinalize.endDate).toLocaleDateString()}
              </p>
              <p className="text-sm mt-1">
                <span className="font-medium">Total Files:</span> {reportToFinalize.totalFiles}
              </p>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowFinalizeDialog(false)
                setReportToFinalize(null)
              }}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmFinalize}
              disabled={processing}
              className="bg-green-600 hover:bg-green-700"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Finalizing...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Finalize Report
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Billing Report</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this billing report? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {reportToDelete && (
            <div className="bg-slate-50 p-4 rounded-md">
              <p className="text-sm">
                <span className="font-medium">Period:</span>{' '}
                {new Date(reportToDelete.startDate).toLocaleDateString()} - {new Date(reportToDelete.endDate).toLocaleDateString()}
              </p>
              <p className="text-sm mt-1">
                <span className="font-medium">Total Files:</span> {reportToDelete.totalFiles}
              </p>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowDeleteDialog(false)
                setReportToDelete(null)
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmDelete}
              variant="destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Report
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default BillingPage
