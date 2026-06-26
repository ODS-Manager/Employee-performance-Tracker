import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { billingApi } from '../../services/api'
import { formatStoredDate, formatStoredDateTime } from '../../utils/helpers'
import type { BillingReport } from '../../types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { ArrowLeft, Download, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export const BillingReportView = () => {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const [report, setReport] = useState<BillingReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !['admin', 'superadmin'].includes(user.userRole)) {
      navigate('/login')
      return
    }
    fetchReport()
  }, [user, id, navigate])

  const fetchReport = async () => {
    if (!id) return

    try {
      setLoading(true)
      const response = await billingApi.get(parseInt(id))
      setReport(response)
    } catch (error: any) {
      console.error('Failed to fetch report:', error)
      toast.error('Failed to load billing report')
      navigate('/admin/billing')
    } finally {
      setLoading(false)
    }
  }

  const handleExportExcel = async () => {
    if (!report) return

    try {
      toast.loading('Generating Excel file...', { id: 'export-excel' })
      await billingApi.exportExcel(report.id)
      toast.success('Excel file downloaded successfully', { id: 'export-excel' })
    } catch (error: any) {
      console.error('Failed to export billing report:', error)
      toast.error(error.response?.data?.detail || 'Failed to export billing report', { id: 'export-excel' })
    }
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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <AdminHeader title="Billing Report" subtitle="View billing report details" />
        <AdminNav />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </main>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-50">
        <AdminHeader title="Billing Report" subtitle="View billing report details" />
        <AdminNav />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <p className="text-muted-foreground">Report not found</p>
          </div>
        </main>
      </div>
    )
  }

  // Group details by team (extract team from product type)
   const teamOrder = [
    'Florida', 'California', 'GI Clearing', 'Washington', 'Michigan',
    'Colorado', 'Utah', 'Oregon', 'Regional Streamline', 'National Streamline',
    'FIF', 'SCB & PD', 'Arizona', 'Texas', 'Pennsylvania', 'Ohio', 'Guam',
    'Georgia', 'Vietnam Team'
  ]

  // Group by team
  const teamData: Record<string, Array<{
    product: string
    directSingleSeat: number
    directStep1: number
    directStep2: number
    agencySingleSeat: number
    agencyStep1: number
    agencyStep2: number
  }>> = {}

   report.details.forEach((detail) => {
    // Use teamName and productName directly from API response
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

  // Sort teams and products
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
    <div className="min-h-screen bg-slate-50">
      <AdminHeader
        title={`${formatStoredDate(report.startDate)} - ${formatStoredDate(report.endDate)} - Billing Report`}
        subtitle="Complete billing report for all teams"
      />
      <AdminNav />

      <main className="container mx-auto px-4 py-8">
        {/* Actions */}
        <div className="flex items-center justify-between mb-6">
          <Button variant="outline" onClick={() => navigate('/admin/billing')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Reports
          </Button>
          <Button onClick={handleExportExcel}>
            <Download className="h-4 w-4 mr-2" />
            Export to Excel
          </Button>
        </div>

        {/* Report Info */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Report Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Period:</span>{' '}
                <span className="font-semibold">
                  {formatStoredDate(report.startDate)} - {formatStoredDate(report.endDate)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Status:</span>{' '}
                {getStatusBadge(report.status)}
              </div>
              <div>
                <span className="text-muted-foreground">Total Files:</span>{' '}
                <span className="font-semibold">{report.totalFiles}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Created By:</span>{' '}
                <span className="font-semibold">{report.createdByName}</span>
              </div>
              {report.finalizedByName && (
                <>
                  <div>
                    <span className="text-muted-foreground">Finalized By:</span>{' '}
                    <span className="font-semibold">{report.finalizedByName}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Finalized At:</span>{' '}
                    <span className="font-semibold">
                      {report.finalizedAt ? formatStoredDateTime(report.finalizedAt, 'en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true,
                      }) : '-'}
                    </span>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Billing Data Table */}
        <Card>
          <CardHeader>
            <CardTitle>Billing Details by Team, Product Type, and Division</CardTitle>
            <CardDescription>Complete breakdown of all teams, product types, and divisions with Single Seat, Step 1, and Step 2 counts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[200px]">Team Name</TableHead>
                    <TableHead className="w-[200px]">Product Type</TableHead>
                    <TableHead className="w-[150px]">Division</TableHead>
                    <TableHead className="w-[150px]">Process Type</TableHead>
                    <TableHead className="text-center w-[100px]">Count</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedTeams.map((teamName) => {
                    const products = teamData[teamName]
                    let teamRowRendered = false

                    return products.map((product) => {
                      const subRows = [
                        { division: 'Direct', label: 'Single Seat', count: product.directSingleSeat },
                        { division: 'Direct', label: 'Step 1', count: product.directStep1 },
                        { division: 'Direct', label: 'Step 2', count: product.directStep2 },
                        { division: 'Agency', label: 'Single Seat', count: product.agencySingleSeat },
                        { division: 'Agency', label: 'Step 1', count: product.agencyStep1 },
                        { division: 'Agency', label: 'Step 2', count: product.agencyStep2 },
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
                            <TableCell className={showTeamName ? 'font-medium align-top' : 'align-top'}>
                              {showTeamName ? teamName : ''}
                            </TableCell>
                            <TableCell className={showProductName ? 'font-medium align-top' : 'align-top'}>
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
                    <TableCell className="text-center">{report.totalFiles}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default BillingReportView
