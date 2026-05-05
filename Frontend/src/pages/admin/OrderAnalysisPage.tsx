import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { Input } from '../../components/ui/input'
import { Badge } from '../../components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { MultiSelect } from '../../components/ui/multi-select'
import { 
  TrendingUp, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Search, 
  RefreshCw,
  Eye,
  Pencil,
  Trash2,
  Download
} from 'lucide-react'
import { ordersApi, teamsApi, referenceApi, metricsApi } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore, getMonthOptions, getYearOptions } from '../../store/dashboardFilterStore'
import { formatStoredDate } from '../../utils/helpers'
import toast from 'react-hot-toast'
import * as XLSX from 'xlsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog'

export const OrderAnalysisPage = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  
  // Get filter state from store
  const {
    filterMonth,
    filterYear,
    filterPeriod,
    setFilterMonth,
    setFilterYear,
    setCurrentMonth,
    setPreviousMonth,
    setFilterPeriod,
  } = useDashboardFilterStore()
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTeamId, setSelectedTeamId] = useState<string>('')
  const [selectedStatusIds, setSelectedStatusIds] = useState<string[]>([])
  const [billingStatusFilter, setBillingStatusFilter] = useState<string[]>([])
  const [stateFilter, setStateFilter] = useState<string[]>([])
  const [productFilter, setProductFilter] = useState<string[]>([])
  const [productionTypeFilter, setProductionTypeFilter] = useState<string[]>([])
  const [processTypeFilter, setProcessTypeFilter] = useState<string[]>([])
  const [transactionTypeFilter, setTransactionTypeFilter] = useState<string[]>([])
  const [propertyTypeFilter, setPropertyTypeFilter] = useState<string[]>([])
  const [startDateFilter, setStartDateFilter] = useState<string>('')
  const [endDateFilter, setEndDateFilter] = useState<string>('')
  
  // Pagination
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Compute effective date range from global filters when no explicit date range is set
  const effectiveStartDate = startDateFilter || `${filterYear}-${filterMonth.padStart(2, '0')}-01`
  const effectiveEndDate = endDateFilter || (() => {
    const lastDay = new Date(parseInt(filterYear), parseInt(filterMonth), 0).getDate()
    return `${filterYear}-${filterMonth.padStart(2, '0')}-${lastDay}`
  })()

  // Selected orders for bulk actions
  const [selectedOrders, setSelectedOrders] = useState<number[]>([])
  const [orderDetailId, setOrderDetailId] = useState<number | null>(null)
  const [orderDetailDialogOpen, setOrderDetailDialogOpen] = useState(false)

  // Delete state
  const [deleteOrderId, setDeleteOrderId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  // Fetch dashboard stats
  const { data: stats } = useQuery({
    queryKey: ['dashboardStats', user?.orgId, selectedTeamId, filterMonth, filterYear],
    queryFn: () => metricsApi.getDashboardStats({ 
      orgId: user?.orgId || undefined,
      teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
      month: parseInt(filterMonth),
      year: parseInt(filterYear),
    }),
  })

  // Fetch orders
  const { data: ordersData, isLoading: loadingOrders, refetch: refetchOrders } = useQuery({
    queryKey: [
      'orders',
      page,
      searchQuery,
      selectedTeamId,
      selectedStatusIds,
      billingStatusFilter,
      stateFilter,
      effectiveStartDate,
      effectiveEndDate,
      filterMonth,
      filterYear,
      user?.orgId,
    ],
    queryFn: () => ordersApi.list({
      orgId: user?.orgId || undefined,
      search: searchQuery || undefined,
      teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
      orderStatusIds: selectedStatusIds.length ? selectedStatusIds.map(id => parseInt(id)) : undefined,
      billingStatuses: billingStatusFilter.length
        ? (billingStatusFilter as Array<'pending' | 'done'>)
        : undefined,
      states: stateFilter.length ? stateFilter : undefined,
      startDate: effectiveStartDate,
      endDate: effectiveEndDate,
      page,
      pageSize,
    }),
  })

  // Fetch ALL orders for stats calculation (no pagination)
  const { data: allOrdersData } = useQuery({
    queryKey: [
      'orders',
      'all-for-stats',
      searchQuery,
      selectedTeamId,
      selectedStatusIds,
      billingStatusFilter,
      stateFilter,
      effectiveStartDate,
      effectiveEndDate,
      filterMonth,
      filterYear,
      user?.orgId,
    ],
    queryFn: () => ordersApi.list({
      orgId: user?.orgId || undefined,
      search: searchQuery || undefined,
      teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
      orderStatusIds: selectedStatusIds.length ? selectedStatusIds.map(id => parseInt(id)) : undefined,
      billingStatuses: billingStatusFilter.length
        ? (billingStatusFilter as Array<'pending' | 'done'>)
        : undefined,
      states: stateFilter.length ? stateFilter : undefined,
      startDate: effectiveStartDate,
      endDate: effectiveEndDate,
      page: 1,
      pageSize: 10000, // Large number to get all orders for stats
    }),
  })

  // Fetch teams for filter
  // For superadmin, don't pass orgId to get all teams
  const { data: teamsData } = useQuery({
    queryKey: ['teams', user?.userRole === 'superadmin' ? 'all' : user?.orgId],
    queryFn: () => teamsApi.list({ 
      orgId: user?.userRole === 'superadmin' ? undefined : user?.orgId || undefined,
      isActive: true
    }),
  })

  // Fetch order statuses for filter
  const { data: orderStatuses } = useQuery({
    queryKey: ['orderStatuses'],
    queryFn: referenceApi.getOrderStatuses,
  })

  // Fetch process types for filter
  const { data: processTypes } = useQuery({
    queryKey: ['processTypes'],
    queryFn: referenceApi.getProcessTypes,
  })

  // Fetch transaction types for filter
  const { data: transactionTypes } = useQuery({
    queryKey: ['transactionTypes'],
    queryFn: referenceApi.getTransactionTypes,
  })

  // Fetch available states for filter
  const { data: availableStates } = useQuery({
    queryKey: ['orderStates', user?.orgId, selectedTeamId],
    queryFn: () => ordersApi.getAvailableStates({
      orgId: user?.orgId,
      teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
    }),
  })

  // Fetch available products for filter
  const { data: availableProducts } = useQuery({
    queryKey: ['orderProducts', user?.orgId, selectedTeamId],
    queryFn: () => ordersApi.getAvailableProducts({
      orgId: user?.orgId,
      teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
    }),
  })

  // Fetch property types for filter
  const { data: propertyTypes } = useQuery({
    queryKey: ['propertyTypes'],
    queryFn: referenceApi.getPropertyTypes,
  })

  // Fetch single order details
  const { data: orderDetail, isLoading: loadingOrderDetail } = useQuery({
    queryKey: ['order', orderDetailId],
    queryFn: () => ordersApi.get(orderDetailId!),
    enabled: !!orderDetailId,
  })

  // Bulk billing status update
  const bulkBillingMutation = useMutation({
    mutationFn: ({ orderIds, status }: { orderIds: number[]; status: 'pending' | 'done' }) =>
      ordersApi.bulkUpdateBillingStatus(orderIds, status),
    onSuccess: () => {
      toast.success('Billing status updated')
      setSelectedOrders([])
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update billing status')
    },
  })

  const orders = ordersData?.items || []
  const allOrders = allOrdersData?.items || []
  const totalOrders = ordersData?.total || 0
  const totalPages = Math.ceil(totalOrders / pageSize)

  useEffect(() => {
    setPage(1)
  }, [
    searchQuery,
    selectedTeamId,
    selectedStatusIds,
    billingStatusFilter,
    stateFilter,
    startDateFilter,
    endDateFilter,
    productFilter,
    productionTypeFilter,
    processTypeFilter,
    transactionTypeFilter,
    propertyTypeFilter,
    filterMonth,
    filterYear,
  ])

  // Filter orders by client-side filters only (server-side filters already applied)
  const filteredOrders = orders.filter(order => {
    // Product filter (client-side)
    if (productFilter.length > 0 && !productFilter.includes(order.productType)) return false
    
    // Production Type filter (client-side)
    if (productionTypeFilter.length > 0 && !productionTypeFilter.includes(order.productionType)) return false
    
    // Process Type filter (client-side)
    if (processTypeFilter.length > 0 && !processTypeFilter.includes(order.processTypeName || '')) return false
    
    // Transaction Type filter (client-side)
    if (transactionTypeFilter.length > 0 && !transactionTypeFilter.includes(order.transactionTypeName || '')) return false
    
    // Property Type filter (client-side)
    if (propertyTypeFilter.length > 0 && !propertyTypeFilter.includes(order.propertyTypeName || '')) return false
    
    return true
  })

  // Filter ALL orders for stats calculation (client-side filters only)
  const allFilteredOrders = allOrders.filter(order => {
    // Product filter (client-side)
    if (productFilter.length > 0 && !productFilter.includes(order.productType)) return false
    
    // Production Type filter (client-side)
    if (productionTypeFilter.length > 0 && !productionTypeFilter.includes(order.productionType)) return false
    
    // Process Type filter (client-side)
    if (processTypeFilter.length > 0 && !processTypeFilter.includes(order.processTypeName || '')) return false
    
    // Transaction Type filter (client-side)
    if (transactionTypeFilter.length > 0 && !transactionTypeFilter.includes(order.transactionTypeName || '')) return false
    
    // Property Type filter (client-side)
    if (propertyTypeFilter.length > 0 && !propertyTypeFilter.includes(order.propertyTypeName || '')) return false
    
    return true
  })

  // Calculate stats from ALL filtered orders (not just current page)
  const filteredStats = {
    totalOrders: allFilteredOrders.length,
    ordersCompleted: allFilteredOrders.filter(o => o.orderStatusName === 'Completed').length,
    ordersOnHold: allFilteredOrders.filter(o => o.orderStatusName === 'On-hold').length,
    ordersBpRti: allFilteredOrders.filter(o => o.orderStatusName === 'BP & RTI').length,
    ordersPendingBilling: allFilteredOrders.filter(o => o.billingStatus === 'pending').length,
  }

  const getStatusBadge = (status: string | null) => {
    if (!status) return 'bg-gray-100 text-gray-800 border-gray-300'
    const statusStyles: { [key: string]: string } = {
      'Completed': 'bg-green-100 text-green-800 border-green-300',
      'On-hold': 'bg-orange-100 text-orange-800 border-orange-300',
      'BP & RTI': 'bg-purple-100 text-purple-800 border-purple-300',
    }
    return statusStyles[status] || 'bg-gray-100 text-gray-800 border-gray-300'
  }

  const formatDate = (dateString: string | null) => {
    return formatStoredDate(dateString, 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const toggleOrderSelection = (orderId: number) => {
    setSelectedOrders(prev =>
      prev.includes(orderId)
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    )
  }

  const toggleAllOrders = () => {
    if (selectedOrders.length === filteredOrders.length) {
      setSelectedOrders([])
    } else {
      setSelectedOrders(filteredOrders.map(o => o.id))
    }
  }

  const handleBulkBillingUpdate = (status: 'pending' | 'done') => {
    if (selectedOrders.length === 0) {
      toast.error('Please select orders first')
      return
    }
    bulkBillingMutation.mutate({ orderIds: selectedOrders, status })
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

  // Export orders to Excel
  const handleExportToExcel = async () => {
    if (allFilteredOrders.length === 0) {
      toast.error('No orders to export')
      return
    }

    const loadingToast = toast.loading(`Exporting ${allFilteredOrders.length} orders...`)

    try {
      // Use the export endpoint to fetch all orders with full details in a single API call
      const exportResult = await ordersApi.export({
        orgId: user?.orgId || undefined,
        search: searchQuery || undefined,
        teamId: selectedTeamId ? parseInt(selectedTeamId) : undefined,
        orderStatusIds: selectedStatusIds.length ? selectedStatusIds.map(id => parseInt(id)) : undefined,
        billingStatuses: billingStatusFilter.length
          ? (billingStatusFilter as Array<'pending' | 'done'>)
          : undefined,
        states: stateFilter.length ? stateFilter : undefined,
        startDate: effectiveStartDate,
        endDate: effectiveEndDate,
        maxRecords: 50000,
      })

      let fullOrders = exportResult.items

      // Apply client-side filters (product, production type, process type, transaction type)
      if (productFilter.length > 0) {
        fullOrders = fullOrders.filter(o => productFilter.includes(o.productType))
      }
      if (productionTypeFilter.length > 0) {
        fullOrders = fullOrders.filter(o => productionTypeFilter.includes(o.productionType))
      }
      if (processTypeFilter.length > 0) {
        fullOrders = fullOrders.filter(o => processTypeFilter.includes(o.processType?.name || ''))
      }
      if (transactionTypeFilter.length > 0) {
        fullOrders = fullOrders.filter(o => transactionTypeFilter.includes(o.transactionType?.name || ''))
      }

      if (fullOrders.length === 0) {
        toast.dismiss(loadingToast)
        toast.error('No orders match the current filters')
        return
      }

      // Prepare data for export with complete details in specified column order
      const exportData = fullOrders.map((order) => {
        return {
          'Date': formatStoredDate(order.entryDate),
          'Order': order.fileNumber,
          'Product Type': order.productType || '-',
          'Production Type': order.productionType || 'regular',
          'Process Type': order.processType?.name || '-',
          'Transaction Type': order.transactionType?.name || '-',
          'State': order.state,
          'Order Status': order.orderStatus?.name || '-',
          'County': order.county || '-',
          'Region': order.division?.name || '-',
          'Step1 FA Name': order.step1?.faName || '-',
          'Step 1 Username': order.step1?.userName || '-',
          'Step2 FA Name': order.step2?.faName || '-',
          'Step 2 Real Name': order.step2?.userName || '-',
          'Property Type': order.propertyType?.name || '-',
          'Employee ID': order.step1?.employeeId || order.step2?.employeeId || '-',
        }
      })

      // Create workbook and worksheet
      const wb = XLSX.utils.book_new()
      const ws = XLSX.utils.json_to_sheet(exportData)

      // Set column widths
      const colWidths = [
        { wch: 12 }, // Date
        { wch: 15 }, // Order
        { wch: 20 }, // Product Type
        { wch: 14 }, // Production Type
        { wch: 18 }, // Process Type
        { wch: 18 }, // Transaction Type
        { wch: 10 }, // State
        { wch: 15 }, // Order Status
        { wch: 15 }, // County
        { wch: 15 }, // Region
        { wch: 18 }, // Step1 FA Name
        { wch: 18 }, // Step 1 Username
        { wch: 18 }, // Step2 FA Name
        { wch: 18 }, // Step 2 Real Name
        { wch: 15 }, // Property Type
        { wch: 14 }, // Employee ID
      ]
      ws['!cols'] = colWidths

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Orders')

      // Generate filename with date range
      const filename = `Orders_${effectiveStartDate}_to_${effectiveEndDate}.xlsx`

      // Save file
      XLSX.writeFile(wb, filename)
      
      toast.dismiss(loadingToast)
      toast.success(`Exported ${fullOrders.length} orders to Excel`)
    } catch (error) {
      console.error('Export error:', error)
      toast.dismiss(loadingToast)
      toast.error('Failed to export orders. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader title="Order Management" subtitle="View and manage all orders" />
      
      <AdminNav />
      
      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid gap-6 md:grid-cols-5 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Orders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                {filteredStats.totalOrders}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5" />
                {filteredStats.ordersCompleted}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">On Hold</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600 flex items-center gap-2">
                <Clock className="h-5 w-5" />
                {filteredStats.ordersOnHold}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">BP & RTI</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                {filteredStats.ordersBpRti}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Pending Billing</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-600">
                {filteredStats.ordersPendingBilling}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg">Filters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Row 1: Search and primary filters */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="relative md:col-span-2">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search by file number, state, county..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={selectedTeamId || 'all'} onValueChange={(val) => setSelectedTeamId(val === 'all' ? '' : val)}>
                <SelectTrigger>
                  <SelectValue placeholder="All Teams" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Teams</SelectItem>
                  {teamsData?.items?.map(team => (
                    <SelectItem key={team.id} value={team.id.toString()}>
                      {team.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

            <MultiSelect
              options={(orderStatuses || [])
                .filter(s => s.isActive !== false)
                .map(status => ({ value: status.id.toString(), label: status.name }))}
              selected={selectedStatusIds}
              onChange={setSelectedStatusIds}
              placeholder="All Status"
              className="w-full"
            />

            <MultiSelect
              options={[
                { value: 'pending', label: 'Pending' },
                { value: 'done', label: 'Done' },
              ]}
              selected={billingStatusFilter}
              onChange={setBillingStatusFilter}
              placeholder="Billing Status"
              className="w-full"
            />
            </div>

            {/* Row 2: Column-specific filters */}
            <div className="grid grid-cols-1 md:grid-cols-8 gap-4">
              {/* Entry Date Range */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Start Date</label>
                <Input
                  type="date"
                  value={startDateFilter}
                  onChange={(e) => setStartDateFilter(e.target.value)}
                  className="h-9"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">End Date</label>
                <Input
                  type="date"
                  value={endDateFilter}
                  onChange={(e) => setEndDateFilter(e.target.value)}
                  className="h-9"
                />
              </div>

              {/* State Filter */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">State</label>
                <MultiSelect
                  options={availableStates || []}
                  selected={stateFilter}
                  onChange={setStateFilter}
                  placeholder="All States"
                  className="w-full"
                />
              </div>

              {/* Product Filter */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Product</label>
                <MultiSelect
                  options={availableProducts || []}
                  selected={productFilter}
                  onChange={setProductFilter}
                  placeholder="All Products"
                  className="w-full"
                />
              </div>

              {/* Production Type Filter (Regular/OT) */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Production Type</label>
                <MultiSelect
                  options={[
                    { value: 'regular', label: 'Regular' },
                    { value: 'OT', label: 'OT' },
                  ]}
                  selected={productionTypeFilter}
                  onChange={setProductionTypeFilter}
                  placeholder="All Types"
                  className="w-full"
                />
              </div>

              {/* Property Type Filter */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Property Type</label>
                <MultiSelect
                  options={(propertyTypes || [])
                    .filter(p => p.isActive !== false)
                    .map(propType => ({ value: propType.name, label: propType.name }))}
                  selected={propertyTypeFilter}
                  onChange={setPropertyTypeFilter}
                  placeholder="All Property Types"
                  className="w-full"
                />
              </div>

              {/* Transaction Type Filter */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Transaction Type</label>
                <MultiSelect
                  options={(transactionTypes || [])
                    .filter(t => t.isActive !== false)
                    .map(type => ({ value: type.name, label: type.name }))}
                  selected={transactionTypeFilter}
                  onChange={setTransactionTypeFilter}
                  placeholder="All Types"
                  className="w-full"
                />
              </div>

              {/* Process Type Filter */}
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 font-medium">Process</label>
                <MultiSelect
                  options={(processTypes || [])
                    .filter(p => p.isActive !== false)
                    .map(process => ({ value: process.name, label: process.name }))}
                  selected={processTypeFilter}
                  onChange={setProcessTypeFilter}
                  placeholder="All Process Types"
                  className="w-full"
                />
              </div>
            </div>

            {/* Clear Filters Button */}
            {(searchQuery || selectedTeamId || selectedStatusIds.length > 0 || billingStatusFilter.length > 0 || stateFilter.length > 0 || productFilter.length > 0 || productionTypeFilter.length > 0 || propertyTypeFilter.length > 0 || processTypeFilter.length > 0 || transactionTypeFilter.length > 0 || startDateFilter || endDateFilter) && (
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('')
                    setSelectedTeamId('')
                    setSelectedStatusIds([])
                    setBillingStatusFilter([])
                    setStateFilter([])
                    setProductFilter([])
                    setProductionTypeFilter([])
                    setPropertyTypeFilter([])
                    setProcessTypeFilter([])
                    setTransactionTypeFilter([])
                    setStartDateFilter('')
                    setEndDateFilter('')
                  }}
                >
                  Clear All Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Bulk Actions */}
        {selectedOrders.length > 0 && (
          <Card className="mb-4 border-blue-200 bg-blue-50">
            <CardContent className="py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {selectedOrders.length} order(s) selected
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleBulkBillingUpdate('done')}
                    disabled={bulkBillingMutation.isPending}
                  >
                    Mark Billing Done
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleBulkBillingUpdate('pending')}
                    disabled={bulkBillingMutation.isPending}
                  >
                    Mark Billing Pending
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedOrders([])}
                  >
                    Clear Selection
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Orders Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Orders</CardTitle>
              <CardDescription>
                Showing {filteredOrders.length} of {totalOrders} orders
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleExportToExcel}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              <Button variant="outline" size="sm" onClick={() => refetchOrders()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingOrders ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <input
                          type="checkbox"
                          checked={selectedOrders.length === filteredOrders.length && filteredOrders.length > 0}
                          onChange={toggleAllOrders}
                          className="rounded border-gray-300"
                        />
                      </TableHead>
                      <TableHead>File Number</TableHead>
                      <TableHead>Entry Date</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Property Type</TableHead>
                      <TableHead>Transaction</TableHead>
                      <TableHead>Division</TableHead>
                      <TableHead>Process</TableHead>
                      <TableHead>Step 1 User</TableHead>
                      <TableHead>Step 2 User</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Billing</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={14} className="text-center py-8 text-gray-500">
                          No orders found
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredOrders.map((order) => (
                        <TableRow key={order.id}>
                          <TableCell>
                            <input
                              type="checkbox"
                              checked={selectedOrders.includes(order.id)}
                              onChange={() => toggleOrderSelection(order.id)}
                              className="rounded border-gray-300"
                            />
                          </TableCell>
                          <TableCell className="font-medium">{order.fileNumber}</TableCell>
                          <TableCell>{formatDate(order.entryDate)}</TableCell>
                          <TableCell>{order.state}</TableCell>
                          <TableCell className="text-xs">{order.productType}</TableCell>
                          <TableCell>
                            <Badge variant={order.productionType === 'OT' ? 'default' : 'outline'}>
                              {order.productionType || 'regular'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs">{order.propertyTypeName || '-'}</TableCell>
                          <TableCell className="text-xs">{order.transactionTypeName || '-'}</TableCell>
                          <TableCell className="text-xs">{order.divisionName || '-'}</TableCell>
                          <TableCell className="text-xs">{order.processTypeName || '-'}</TableCell>
                          <TableCell className="text-xs">{order.step1UserName || '-'}</TableCell>
                          <TableCell className="text-xs">{order.step2UserName || '-'}</TableCell>
                          <TableCell>
                            <Badge className={getStatusBadge(order.orderStatusName)}>
                              {order.orderStatusName || 'Unknown'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={order.billingStatus === 'done' ? 'default' : 'secondary'}>
                              {order.billingStatus}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {user?.userRole?.toLowerCase() !== 'superadmin' && order.billingStatus !== 'done' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => navigate(`/examiner/edit-order/${order.id}`)}
                                  title="Edit Order"
                                >
                                  <Pencil className="h-4 w-4" />
                                </Button>
                              )}
                              {(user?.userRole === 'admin' || user?.userRole === 'superadmin') && order.billingStatus !== 'done' && (
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
                              <Dialog 
                                open={orderDetailDialogOpen} 
                                onOpenChange={(open) => {
                                  setOrderDetailDialogOpen(open)
                                  if (!open) setOrderDetailId(null)
                                }}
                              >
                                <DialogTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setOrderDetailId(order.id)
                                      setOrderDetailDialogOpen(true)
                                    }}
                                    title="View Details"
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-2xl">
                                  <DialogHeader>
                                    <DialogTitle>Order Details - {order.fileNumber}</DialogTitle>
                                    <DialogDescription>
                                      View order details and step information
                                    </DialogDescription>
                                  </DialogHeader>
                                  {loadingOrderDetail ? (
                                    <div className="flex items-center justify-center py-8">
                                      <Loader2 className="h-6 w-6 animate-spin" />
                                    </div>
                                  ) : orderDetail ? (
                                    <div className="space-y-6">
                                       {/* Order Info */}
                                      <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                          <span className="text-gray-500">File Number:</span>
                                          <span className="ml-2 font-medium">{orderDetail.fileNumber}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Entry Date:</span>
                                          <span className="ml-2">{formatDate(orderDetail.entryDate)}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">State:</span>
                                          <span className="ml-2">{orderDetail.state}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Product:</span>
                                          <span className="ml-2">{orderDetail.productType}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Property Type:</span>
                                          <span className="ml-2">{orderDetail.propertyType?.name || '-'}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Transaction Type:</span>
                                          <span className="ml-2">{orderDetail.transactionType?.name || '-'}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Division:</span>
                                          <span className="ml-2">{orderDetail.division?.name || '-'}</span>
                                        </div>
                                        <div>
                                          <span className="text-gray-500">Status:</span>
                                          <Badge className={`ml-2 ${getStatusBadge(orderDetail.orderStatus?.name || null)}`}>
                                            {orderDetail.orderStatus?.name || 'Unknown'}
                                          </Badge>
                                        </div>
                                      </div>

                                      {/* Step 1 Info */}
                                      <div className="border rounded-lg p-4 bg-blue-50/50">
                                        <h4 className="font-medium text-blue-900 mb-3">Step 1</h4>
                                        <div className="grid grid-cols-1 gap-2 text-sm">
                                          <div>
                                            <span className="text-gray-500">User:</span>
                                            <span className="ml-2">{orderDetail.step1?.userName || 'Not assigned'}</span>
                                          </div>
                                        </div>
                                      </div>

                                      {/* Step 2 Info */}
                                      <div className="border rounded-lg p-4 bg-green-50/50">
                                        <h4 className="font-medium text-green-900 mb-3">Step 2</h4>
                                        <div className="grid grid-cols-1 gap-2 text-sm">
                                          <div>
                                            <span className="text-gray-500">User:</span>
                                            <span className="ml-2">{orderDetail.step2?.userName || 'Not assigned'}</span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  ) : null}
                                </DialogContent>
                              </Dialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <span className="text-sm text-gray-500">
                      Page {page} of {totalPages}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
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

export default OrderAnalysisPage
