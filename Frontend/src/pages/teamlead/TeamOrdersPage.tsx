import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { useTeamLeadFilterStore } from '../../store/teamLeadFilterStore'
import { useDashboardFilterStore } from '../../store/dashboardFilterStore'
import { teamsApi, ordersApi, referenceApi } from '../../services/api'
import { formatStoredDate, formatStoredDateTime, getInitials, handleLogoutFlow, parseStoredDateToUtcDate } from '../../utils/helpers'
import type { OrderSimple, ProcessType, Division, OrderStatus } from '../../types'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { TeamLeadNav } from '../../components/layout/TeamLeadNav'
import { GlobalFilters } from '../../components/filters/GlobalFilters'
import { HeaderRefreshButton } from '../../components/common/HeaderRefreshButton'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Calendar } from '../../components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover'
import * as XLSX from 'xlsx'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select'
import { MultiSelect } from '../../components/ui/multi-select'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../../components/ui/dropdown-menu'
import { 
  FileText, 
  CheckCircle2,
  Clock,
  AlertCircle,

  LogOut,
  Loader2,
  Users,
  Shield,
  Plus,
  Edit,
  Trash2,
  Filter,
  Calendar as CalendarIcon,
  RotateCcw,
  Download
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog'
import odsLogo from '../../assets/ods-logo.png'
import { cn } from '../../lib/utils'

export const TeamOrdersPage = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { selectedTeamId, setSelectedTeamId } = useTeamLeadFilterStore()
  const { filterMonth, filterYear } = useDashboardFilterStore()
  
  const isAdminOrSuperadmin = user?.userRole === 'admin' || user?.userRole === 'superadmin'

  // Delete state
  const [deleteOrderId, setDeleteOrderId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [billingFilter, setBillingFilter] = useState<string[]>([])
  const [stateFilter, setStateFilter] = useState<string[]>([])
  const [productTypeFilter, setProductTypeFilter] = useState<string[]>([])
  const [productionTypeFilter, setProductionTypeFilter] = useState<string[]>([])
  const [processTypeFilter, setProcessTypeFilter] = useState<string[]>([])
  const [divisionFilter, setDivisionFilter] = useState<string[]>([])
  const [orderStatusFilter, setOrderStatusFilter] = useState<string[]>([])
  const [faNameFilter, setFaNameFilter] = useState<string[]>([])
  
  // Date range - derived from global filters, with optional local overrides
  const [startDateOverride, setStartDateOverride] = useState<string>('')
  const [endDateOverride, setEndDateOverride] = useState<string>('')
  
  // Compute effective dates from global filter or local override
  const defaultStartDate = `${filterYear}-${filterMonth.padStart(2, '0')}-01`
  const defaultEndDate = (() => {
    const lastDay = new Date(parseInt(filterYear), parseInt(filterMonth), 0).getDate()
    return `${filterYear}-${filterMonth.padStart(2, '0')}-${lastDay}`
  })()

  const startDate = startDateOverride || defaultStartDate
  const endDate = endDateOverride || defaultEndDate
  
  // Show/hide filter panel
  const [showFilters, setShowFilters] = useState<boolean>(true)

  // Clear local date overrides when global filters change
  useEffect(() => {
    setStartDateOverride('')
    setEndDateOverride('')
  }, [filterMonth, filterYear])

  // Redirect if not team lead
  if (!user || user.userRole !== 'team_lead') {
    navigate('/login')
    return null
  }

  // Get all teams the team lead manages
  const { data: teamsData, isLoading: _loadingTeams } = useQuery({
    queryKey: ['teams', 'my-teams', user?.id],
    queryFn: () => teamsApi.myTeams(),
    enabled: !!user && user.userRole === 'team_lead',
  })

  const myTeams = teamsData?.items || []
  
  // Auto-select first team if none selected or selected team is not in the list
  const teamId = selectedTeamId && myTeams.some(t => t.id === selectedTeamId) 
    ? selectedTeamId 
    : myTeams[0]?.id || null

  // Update selected team if it changes
  if (teamId && teamId !== selectedTeamId) {
    setSelectedTeamId(teamId)
  }

  const currentTeam = myTeams.find(t => t.id === teamId)

  const productOptions = Array.from(
    new Set(
      (currentTeam?.products || [])
        .map((product: unknown) => {
          if (typeof product === 'string') return product
          if (
            product &&
            typeof product === 'object' &&
            'productType' in product &&
            typeof (product as { productType?: unknown }).productType === 'string'
          ) {
            return (product as { productType: string }).productType
          }
          return ''
        })
        .filter((productType): productType is string => Boolean(productType))
    )
  )

  // Fetch reference data for filters
  const { data: processTypes = [] } = useQuery<ProcessType[]>({
    queryKey: ['process-types'],
    queryFn: referenceApi.getProcessTypes,
  })

  const { data: divisions = [] } = useQuery<Division[]>({
    queryKey: ['divisions'],
    queryFn: referenceApi.getDivisions,
  })

  const { data: orderStatuses = [] } = useQuery<OrderStatus[]>({
    queryKey: ['order-statuses'],
    queryFn: referenceApi.getOrderStatuses,
  })

  // Get unique states from current team
  const availableStates = currentTeam?.states || []

  // Fetch FA names for the team
  const { data: faNamesData, isLoading: faNamesLoading } = useQuery({
    queryKey: ['faNames', teamId],
    queryFn: () => teamsApi.getFaNames(teamId!),
    enabled: !!teamId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  const faNames = faNamesData?.items || []

  // Fetch team orders
  const { data: ordersData, isLoading: loadingOrders, refetch: refetchOrders } = useQuery({
    queryKey: [
      'orders',
      'team',
      teamId,
      startDate,
      endDate,
      statusFilter,
      billingFilter,
      stateFilter,
      processTypeFilter,
      divisionFilter,
      orderStatusFilter,
      faNameFilter,
      productTypeFilter,
      productionTypeFilter,
    ],
    queryFn: () => ordersApi.list({
      teamId: teamId!,
      startDate,
      endDate,
      billingStatuses: billingFilter.length ? (billingFilter as Array<'pending' | 'done'>) : undefined,
      states: stateFilter.length ? stateFilter : undefined,
      processTypeIds: processTypeFilter.length ? processTypeFilter.map(id => parseInt(id)) : undefined,
      divisionIds: divisionFilter.length ? divisionFilter.map(id => parseInt(id)) : undefined,
      orderStatusIds: orderStatusFilter.length ? orderStatusFilter.map(id => parseInt(id)) : undefined,
      faNames: faNameFilter.length ? faNameFilter : undefined,
      pageSize: 10000, // Increased to fetch more orders
    }),
    enabled: !!teamId,
  })

  const orders = ordersData?.items || []

  const getWorkStatus = (order: OrderSimple) => {
    if (order.step1UserId && order.step2UserId) return 'completed'
    if (order.step1UserId || order.step2UserId) return 'in_progress'
    return 'pending'
  }

  // Filter orders based on work status (completed/in-progress/pending based on step assignments)
  const filteredOrders = orders.filter(order => {
    // Work Status filter
    if (statusFilter.length > 0 && !statusFilter.includes(getWorkStatus(order))) return false
    
    // Product Type filter
    if (productTypeFilter.length > 0 && !productTypeFilter.includes(order.productType)) return false
    
    // Production Type filter
    if (productionTypeFilter.length > 0 && !productionTypeFilter.includes(order.productionType)) return false
    
    return true
  })

  // Stats
  const completedOrders = orders.filter(o => o.step1UserId && o.step2UserId).length
  const inProgressOrders = orders.filter(o => (o.step1UserId && !o.step2UserId) || (!o.step1UserId && o.step2UserId)).length
  const pendingBilling = orders.filter(
    o => o.billingStatus === 'pending' && o.orderStatusName?.toLowerCase() === 'completed'
  ).length

  const handleLogout = async () => {
    await handleLogoutFlow(logout, navigate)
  }

  const handleDeleteOrder = async (orderId: number) => {
    setDeleting(true)
    try {
      await ordersApi.delete(orderId)
      toast.success('Order deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      setDeleteOrderId(null)
    } catch (error: any) {
      const msg = error.response?.data?.detail || 'Failed to delete order'
      toast.error(msg)
    } finally {
      setDeleting(false)
    }
  }

  const getOrderStatusBadge = (order: OrderSimple) => {
    const status = order.orderStatusName?.toLowerCase() || ''
    if (status === 'completed') {
      return <Badge className="bg-green-100 text-green-800">Completed</Badge>
    } else if (status === 'on-hold') {
      return <Badge className="bg-orange-100 text-orange-800">On-hold</Badge>
    } else if (status === 'bp & rti') {
      return <Badge className="bg-purple-100 text-purple-800">BP & RTI</Badge>
    } else if (status === 'in progress') {
      return <Badge className="bg-blue-100 text-blue-800">In Progress</Badge>
    }
    return <Badge className="bg-gray-100 text-gray-800">{order.orderStatusName || 'Unknown'}</Badge>
  }

  const getBillingBadge = (status: string) => {
    if (status === 'done') {
      return <Badge className="bg-green-100 text-green-800">Done</Badge>
    }
    return <Badge variant="outline" className="text-orange-600 border-orange-300">Pending</Badge>
  }

  // Reset all filters
  const resetFilters = () => {
    setStatusFilter([])
    setBillingFilter([])
    setStateFilter([])
    setProductTypeFilter([])
    setProductionTypeFilter([])
    setProcessTypeFilter([])
    setDivisionFilter([])
    setOrderStatusFilter([])
    setFaNameFilter([])
    setStartDateOverride('')
    setEndDateOverride('')
  }

  // Export to Excel with full order details
  const handleExportToExcel = async () => {
    if (filteredOrders.length === 0) {
      toast.error('No orders to export')
      return
    }

    const loadingToast = toast.loading(`Exporting ${filteredOrders.length} orders...`)

    try {
      // Use the export endpoint to fetch all orders with full details in a single API call
      const exportResult = await ordersApi.export({
        teamId: teamId!,
        startDate,
        endDate,
        billingStatuses: billingFilter.length ? (billingFilter as Array<'pending' | 'done'>) : undefined,
        states: stateFilter.length ? stateFilter : undefined,
        processTypeIds: processTypeFilter.length ? processTypeFilter.map(id => parseInt(id)) : undefined,
        divisionIds: divisionFilter.length ? divisionFilter.map(id => parseInt(id)) : undefined,
        orderStatusIds: orderStatusFilter.length ? orderStatusFilter.map(id => parseInt(id)) : undefined,
        faNames: faNameFilter.length ? faNameFilter : undefined,
        maxRecords: 50000,
      })

      let fullOrders = exportResult.items

      // Apply client-side filters
      if (statusFilter.length > 0) {
        fullOrders = fullOrders.filter(order => {
          const workStatus = order.step1?.userId && order.step2?.userId
            ? 'completed'
            : (order.step1?.userId || order.step2?.userId)
              ? 'in_progress'
              : 'pending'
          return statusFilter.includes(workStatus)
        })
      }
      
      // Apply product type filter
      if (productTypeFilter.length > 0) {
        fullOrders = fullOrders.filter(order => productTypeFilter.includes(order.productType))
      }
      
      // Apply production type filter
      if (productionTypeFilter.length > 0) {
        fullOrders = fullOrders.filter(order => productionTypeFilter.includes(order.productionType))
      }

      if (fullOrders.length === 0) {
        toast.dismiss(loadingToast)
        toast.error('No orders match the current filters')
        return
      }

      // Prepare data for export with complete details
      const exportData = fullOrders.map((order) => {
        // Format timestamps
        const formatDateTime = (dateStr: string | null) => {
          return formatStoredDateTime(dateStr, 'en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })
        }

        return {
          'File Number': order.fileNumber,
          'Entry Date': formatStoredDate(order.entryDate),
          'State': order.state,
          'County': order.county,
          'Product Type': order.productType,
          'Production Type': order.productionType || 'regular',
          'Transaction Type': order.transactionType?.name || '-',
          'Process Type': order.processType?.name || '-',
          'Division': order.division?.name || '-',
          'Order Status': order.orderStatus?.name || '-',
          'Billing Status': order.billingStatus === 'done' ? 'Done' : 'Pending',
          'Work Status': order.step1?.userId && order.step2?.userId ? 'Completed' : 
                         (order.step1?.userId || order.step2?.userId) ? 'In Progress' : 'Pending',
          'Step 1 User': order.step1?.userName || '-',
          'Step 1 FA Name': order.step1?.faName || '-',
          'Step 2 User': order.step2?.userName || '-',
          'Step 2 FA Name': order.step2?.faName || '-',
          'Created At': formatDateTime(order.createdAt),
          'Modified At': formatDateTime(order.modifiedAt),
        }
      })

      // Create workbook and worksheet
      const wb = XLSX.utils.book_new()
      const ws = XLSX.utils.json_to_sheet(exportData)

      // Set column widths
      const colWidths = [
        { wch: 15 }, // File Number
        { wch: 12 }, // Entry Date
        { wch: 10 }, // State
        { wch: 15 }, // County
        { wch: 20 }, // Product Type
        { wch: 12 }, // Production Type
        { wch: 18 }, // Transaction Type
        { wch: 15 }, // Process Type
        { wch: 15 }, // Division
        { wch: 15 }, // Order Status
        { wch: 15 }, // Billing Status
        { wch: 15 }, // Work Status
        { wch: 15 }, // Step 1 User
        { wch: 15 }, // Step 1 FA Name
        { wch: 20 }, // Step 1 Start Time
        { wch: 20 }, // Step 1 End Time
        { wch: 15 }, // Step 2 User
        { wch: 15 }, // Step 2 FA Name
        { wch: 20 }, // Step 2 Start Time
        { wch: 20 }, // Step 2 End Time
        { wch: 20 }, // Created At
        { wch: 20 }, // Modified At
      ]
      ws['!cols'] = colWidths

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Orders')

      // Generate filename
      const teamName = currentTeam?.name || 'Team'
      const dateRange = `${startDate}_to_${endDate}`
      const filename = `${teamName}_Orders_${dateRange}.xlsx`

      // Save file
      XLSX.writeFile(wb, filename)
      
      toast.dismiss(loadingToast)
      toast.success(`Exported ${fullOrders.length} orders with complete details to Excel`)
    } catch (error) {
      console.error('Export error:', error)
      toast.dismiss(loadingToast)
      toast.error('Failed to export orders. Please try again.')
    }
  }

  // Format date range for display
  const formatDateRange = () => {
    return `${formatStoredDate(startDate, 'en-US', { month: 'short', day: 'numeric' })} - ${formatStoredDate(endDate, 'en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  }

  // Count active filters
  const activeFilterCount = [
    statusFilter.length > 0,
    billingFilter.length > 0,
    stateFilter.length > 0,
    productTypeFilter.length > 0,
    productionTypeFilter.length > 0,
    processTypeFilter.length > 0,
    divisionFilter.length > 0,
    orderStatusFilter.length > 0,
    faNameFilter.length > 0,
  ].filter(Boolean).length

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={odsLogo} alt="ODS Logo" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Team Orders</h1>
                <p className="text-sm text-slate-600">
                  {formatDateRange()}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Team Filter */}
              {myTeams.length > 1 && (
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-slate-600" />
                  <Select 
                    value={teamId?.toString() || ''} 
                    onValueChange={(value) => setSelectedTeamId(parseInt(value))}
                  >
                    <SelectTrigger className="w-[220px]">
                      <SelectValue placeholder="Select team" />
                    </SelectTrigger>
                    <SelectContent>
                      {myTeams.map((team) => (
                        <SelectItem key={team.id} value={team.id.toString()}>
                          {team.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {myTeams.length === 1 && currentTeam && (
                <Badge variant="outline" className="px-3 py-1">
                  <Users className="w-3 h-3 mr-1" />
                  {currentTeam.name}
                </Badge>
              )}
              
              <GlobalFilters showOrgFilter={false} />

              <Button onClick={() => navigate('/examiner/new-order')}>
                <Plus className="mr-2 h-4 w-4" />
                New Order
              </Button>

              <HeaderRefreshButton />
               
              <Badge variant="outline" className="px-3 py-1">
                <Shield className="w-3 h-3 mr-1" />
                Team Lead
              </Badge>
              
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
        {loadingOrders ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : !teamId ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">You are not currently leading any team.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Total Orders
                  </CardTitle>
                  <FileText className="h-5 w-5 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">{orders.length}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Completed
                  </CardTitle>
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">{completedOrders}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    In Progress
                  </CardTitle>
                  <Clock className="h-5 w-5 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">{inProgressOrders}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Pending Billing
                  </CardTitle>
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-900">{pendingBilling}</div>
                </CardContent>
              </Card>
            </div>

            {/* Filters and Orders Table */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Orders</CardTitle>
                    <CardDescription>Showing {filteredOrders.length} of {ordersData?.total || orders.length} orders</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => refetchOrders()}
                      disabled={loadingOrders}
                    >
                      <RotateCcw className={`h-4 w-4 mr-2 ${loadingOrders ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleExportToExcel}
                      disabled={filteredOrders.length === 0}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export to Excel
                    </Button>
                    <Button
                      variant={showFilters ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowFilters(!showFilters)}
                    >
                      <Filter className="h-4 w-4 mr-2" />
                      Filters
                      {activeFilterCount > 0 && (
                        <Badge variant="secondary" className="ml-2 bg-white text-primary">
                          {activeFilterCount}
                        </Badge>
                      )}
                    </Button>
                    {activeFilterCount > 0 && (
                      <Button variant="ghost" size="sm" onClick={resetFilters}>
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Reset
                      </Button>
                    )}
                  </div>
                </div>

                {/* Comprehensive Filters Panel */}
                {showFilters && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-9 gap-4">
                      {/* Date Range */}
                      <Popover>
                        <div className="space-y-2 md:col-span-2 lg:col-span-2">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="startDate" className="text-xs font-medium text-slate-600">
                              From Date
                            </Label>
                            <PopoverTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 text-slate-600"
                                aria-label="Pick start date"
                              >
                                <CalendarIcon className="h-3 w-3" />
                              </Button>
                            </PopoverTrigger>
                          </div>
                          <PopoverTrigger asChild>
                            <Button
                              id="startDate"
                              variant="outline"
                              className={cn(
                                "h-9 w-full min-w-[220px] justify-start text-left font-normal",
                                !startDate && "text-muted-foreground"
                              )}
                              >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                              {startDate ? formatStoredDate(startDate, 'en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : <span>Pick a date</span>}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={startDate ? parseStoredDateToUtcDate(startDate) ?? undefined : undefined}
                              onSelect={(date) => {
                                if (!date) return
                                setStartDateOverride(format(date, 'yyyy-MM-dd'))
                              }}
                              initialFocus
                            />
                          </PopoverContent>
                        </div>
                      </Popover>
                      
                      <Popover>
                        <div className="space-y-2 md:col-span-2 lg:col-span-2">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="endDate" className="text-xs font-medium text-slate-600">
                              To Date
                            </Label>
                            <PopoverTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 text-slate-600"
                                aria-label="Pick end date"
                              >
                                <CalendarIcon className="h-3 w-3" />
                              </Button>
                            </PopoverTrigger>
                          </div>
                          <PopoverTrigger asChild>
                            <Button
                              id="endDate"
                              variant="outline"
                              className={cn(
                                "h-9 w-full min-w-[220px] justify-start text-left font-normal",
                                !endDate && "text-muted-foreground"
                              )}
                              >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                              {endDate ? formatStoredDate(endDate, 'en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : <span>Pick a date</span>}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                              mode="single"
                              selected={endDate ? parseStoredDateToUtcDate(endDate) ?? undefined : undefined}
                              onSelect={(date) => {
                                if (!date) return
                                setEndDateOverride(format(date, 'yyyy-MM-dd'))
                              }}
                              disabled={parseStoredDateToUtcDate(startDate) ? { before: parseStoredDateToUtcDate(startDate)! } : undefined}
                              initialFocus
                            />
                          </PopoverContent>
                        </div>
                      </Popover>

                      {/* Work Status Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Work Status</Label>
                        <MultiSelect
                          options={[
                            { value: 'completed', label: 'Completed' },
                            { value: 'in_progress', label: 'In Progress' },
                            { value: 'pending', label: 'Pending' },
                          ]}
                          selected={statusFilter}
                          onChange={setStatusFilter}
                          placeholder="All Status"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Billing Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Billing Status</Label>
                        <MultiSelect
                          options={[
                            { value: 'pending', label: 'Pending' },
                            { value: 'done', label: 'Done' },
                          ]}
                          selected={billingFilter}
                          onChange={setBillingFilter}
                          placeholder="All Billing Statuses"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* State Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">State</Label>
                        <MultiSelect
                          options={availableStates.map((stateObj) => stateObj.state)}
                          selected={stateFilter}
                          onChange={setStateFilter}
                          placeholder="All States"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Product Type Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Product</Label>
                        <MultiSelect
                          options={productOptions}
                          selected={productTypeFilter}
                          onChange={setProductTypeFilter}
                          placeholder="All Products"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Production Type Filter (Regular/OT) */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Production Type</Label>
                        <MultiSelect
                          options={[
                            { value: 'regular', label: 'Regular' },
                            { value: 'OT', label: 'OT' },
                          ]}
                          selected={productionTypeFilter}
                          onChange={setProductionTypeFilter}
                          placeholder="All Types"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Process Type Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Process Type</Label>
                        <MultiSelect
                          options={processTypes
                            .filter(pt => pt.isActive !== false)
                            .map(pt => ({ value: pt.id.toString(), label: pt.name }))}
                          selected={processTypeFilter}
                          onChange={setProcessTypeFilter}
                          placeholder="All Process Types"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Division Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Division</Label>
                        <MultiSelect
                          options={divisions.map(div => ({ value: div.id.toString(), label: div.name }))}
                          selected={divisionFilter}
                          onChange={setDivisionFilter}
                          placeholder="All Divisions"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* Order Status Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">Order Status</Label>
                        <MultiSelect
                          options={orderStatuses
                            .filter(os => os.isActive !== false)
                            .map(os => ({ value: os.id.toString(), label: os.name }))}
                          selected={orderStatusFilter}
                          onChange={setOrderStatusFilter}
                          placeholder="All Order Statuses"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                        />
                      </div>

                      {/* FA Name Filter */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-slate-600">FA Name</Label>
                        <MultiSelect
                          options={faNames.map((fn) => fn.faName)}
                          selected={faNameFilter}
                          onChange={setFaNameFilter}
                          placeholder="All FA Names"
                          className="w-full"
                          triggerClassName="min-h-9 h-9 text-xs"
                          disabled={faNamesLoading}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>File Number</TableHead>
                      <TableHead>Entry Date</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>County</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Division</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Billing</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                          <p>No orders found for the selected filters</p>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredOrders.map((order: OrderSimple) => (
                        <TableRow key={order.id}>
                          <TableCell className="font-medium font-mono">
                            {order.fileNumber}
                          </TableCell>
                          <TableCell>
                            {formatStoredDate(order.entryDate)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{order.state}</Badge>
                          </TableCell>
                          <TableCell>{order.county}</TableCell>
                          <TableCell>
                            <Badge variant="secondary">{order.productType}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={order.productionType === 'OT' ? 'default' : 'outline'}>
                              {order.productionType || 'regular'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{order.divisionName || '-'}</Badge>
                          </TableCell>
                          <TableCell>
                            {getOrderStatusBadge(order)}
                          </TableCell>
                          <TableCell>
                            {getBillingBadge(order.billingStatus)}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              {order.billingStatus !== 'done' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => navigate(`/examiner/edit-order/${order.id}`)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              )}
                              {isAdminOrSuperadmin && order.billingStatus !== 'done' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteOrderId(order.id)}
                                title="Delete Order"
                                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                
                {/* Pagination info */}
                {ordersData && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      Showing {filteredOrders.length} of {orders.length} orders
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Total: {ordersData.total} orders
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteOrderId !== null} onOpenChange={(open) => { if (!open) setDeleteOrderId(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Order</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this order? This action can be reversed by an admin (restore).
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteOrderId(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteOrderId && handleDeleteOrder(deleteOrderId)}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TeamOrdersPage
