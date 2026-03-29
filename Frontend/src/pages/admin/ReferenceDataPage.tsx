import { useState, useEffect, useCallback } from 'react'
import { AdminNav } from '../../components/layout/AdminNav'
import { AdminHeader } from '../../components/layout/AdminHeader'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Badge } from '../../components/ui/badge'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select'
import { 
  Loader2, 
  Plus, 
  Edit2, 
  Trash2, 
  Settings,
  Info,
} from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'
import { referenceApi, duplicateConfigApi } from '../../services/api'
import { faNamesApi } from '../../services/api'
import type { FAName, AllowedDuplicateProduct } from '../../types'

type TransactionType = { id: number; name: string; isActive: boolean }
type OrderStatus = { id: number; name: string; isActive: boolean }
type ProductType = { id: number; name: string; isActive: boolean }
type PropertyType = { id: number; name: string; isActive: boolean }
type State = { id: number; code: string; name: string; isActive: boolean }

interface ReferenceItem {
  id: number
  name: string
  isActive?: boolean
  code?: string
}

export const ReferenceDataPage = () => {
  const [activeTab, setActiveTab] = useState('transaction-types')
  
  // Product Types (from team_products)
  const [productTypes, setProductTypes] = useState<ProductType[]>([])
  const [productTypesLoading, setProductTypesLoading] = useState(true)
  
  // States (from team_states)
  const [states, setStates] = useState<State[]>([])
  const [statesLoading, setStatesLoading] = useState(true)
  
  // FA Names
  const [faNames, setFaNames] = useState<FAName[]>([])
  const [faNamesLoading, setFaNamesLoading] = useState(true)
  
  // Transaction Types
  const [transactionTypes, setTransactionTypes] = useState<TransactionType[]>([])
  const [transactionTypesLoading, setTransactionTypesLoading] = useState(true)
  
  // Order Statuses
  const [orderStatuses, setOrderStatuses] = useState<OrderStatus[]>([])
  const [orderStatusesLoading, setOrderStatusesLoading] = useState(true)

  // Property Types
  const [propertyTypes, setPropertyTypes] = useState<PropertyType[]>([])
  const [propertyTypesLoading, setPropertyTypesLoading] = useState(true)

  // Allowed Duplicate Products
  const [duplicateProducts, setDuplicateProducts] = useState<AllowedDuplicateProduct[]>([])
  const [duplicateProductsLoading, setDuplicateProductsLoading] = useState(true)

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [currentType, setCurrentType] = useState('')
  const [selectedItem, setSelectedItem] = useState<ReferenceItem | null>(null)
  
  // Form states
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    isActive: true
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fetchProductTypes = useCallback(async () => {
    try {
      const data = await referenceApi.getProductTypes()
      setProductTypes(data)
    } catch (error) {
      console.error('Failed to fetch product types:', error)
      toast.error('Failed to load product types')
    } finally {
      setProductTypesLoading(false)
    }
  }, [])

  const fetchStates = useCallback(async () => {
    try {
      const data = await referenceApi.getStates()
      setStates(data)
    } catch (error) {
      console.error('Failed to fetch states:', error)
      toast.error('Failed to load states')
    } finally {
      setStatesLoading(false)
    }
  }, [])

  const fetchFaNames = useCallback(async () => {
    try {
      const data = await faNamesApi.list({ limit: 500 })
      setFaNames(data.items)
    } catch (error) {
      console.error('Failed to fetch FA names:', error)
      toast.error('Failed to load FA names')
    } finally {
      setFaNamesLoading(false)
    }
  }, [])

  const fetchTransactionTypes = useCallback(async () => {
    try {
      const data = await referenceApi.getTransactionTypes()
      setTransactionTypes(data)
    } catch (error) {
      console.error('Failed to fetch transaction types:', error)
      toast.error('Failed to load transaction types')
    } finally {
      setTransactionTypesLoading(false)
    }
  }, [])

  const fetchOrderStatuses = useCallback(async () => {
    try {
      const data = await referenceApi.getOrderStatuses()
      setOrderStatuses(data)
    } catch (error) {
      console.error('Failed to fetch order statuses:', error)
      toast.error('Failed to load order statuses')
    } finally {
      setOrderStatusesLoading(false)
    }
  }, [])

  const fetchPropertyTypes = useCallback(async () => {
    try {
      const data = await referenceApi.getPropertyTypes()
      setPropertyTypes(data)
    } catch (error) {
      console.error('Failed to fetch property types:', error)
      toast.error('Failed to load property types')
    } finally {
      setPropertyTypesLoading(false)
    }
  }, [])

  const fetchDuplicateProducts = useCallback(async () => {
    try {
      const data = await duplicateConfigApi.getAll()
      setDuplicateProducts(data.items)
    } catch (error) {
      console.error('Failed to fetch duplicate products:', error)
      toast.error('Failed to load duplicate product settings')
    } finally {
      setDuplicateProductsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (activeTab === 'product-types') fetchProductTypes()
    if (activeTab === 'states') fetchStates()
    if (activeTab === 'fa-names') fetchFaNames()
    if (activeTab === 'transaction-types') fetchTransactionTypes()
    if (activeTab === 'order-statuses') fetchOrderStatuses()
    if (activeTab === 'property-types') fetchPropertyTypes()
    if (activeTab === 'duplicate-settings') {
      fetchDuplicateProducts()
      // Also fetch product types for the dropdown
      if (productTypes.length === 0) fetchProductTypes()
    }
  }, [activeTab, fetchProductTypes, fetchStates, fetchFaNames, fetchTransactionTypes, fetchOrderStatuses, fetchPropertyTypes, fetchDuplicateProducts, productTypes.length])

  const handleOpenEdit = (type: string, item: ReferenceItem) => {
    setCurrentType(type)
    setSelectedItem(item)
    setFormData({
      name: item.name || '',
      code: item.code || '',
      isActive: item.isActive ?? true
    })
    setEditDialogOpen(true)
  }

  const handleOpenDelete = (type: string, item: ReferenceItem) => {
    setCurrentType(type)
    setSelectedItem(item)
    setDeleteDialogOpen(true)
  }

  const handleOpenAdd = (type: string) => {
    setCurrentType(type)
    setSelectedItem(null)
    setFormData({ name: '', code: '', isActive: true })
    setEditDialogOpen(true)
  }

  const handleSubmit = async () => {
    // Validation for duplicate-settings dropdown
    if (currentType === 'duplicate-settings' && !selectedItem && !formData.name) {
      toast.error('Please select a product type')
      return
    }
    
    if (!formData.name.trim() && !formData.code?.trim()) {
      toast.error('Name is required')
      return
    }

    setIsSubmitting(true)
    try {
      switch (currentType) {
        case 'fa-names':
          if (selectedItem) {
            await faNamesApi.update(selectedItem.id, { name: formData.name, isActive: formData.isActive })
            toast.success('FA name updated')
          } else {
            await faNamesApi.create({ name: formData.name })
            toast.success('FA name created')
          }
          fetchFaNames()
          break
          
        case 'transaction-types':
          if (selectedItem) {
            await referenceApi.updateTransactionType(selectedItem.id, { name: formData.name, isActive: formData.isActive })
            toast.success('Transaction type updated')
          } else {
            await referenceApi.createTransactionType(formData.name)
            toast.success('Transaction type created')
          }
          fetchTransactionTypes()
          break
          
        case 'order-statuses':
          if (selectedItem) {
            await referenceApi.updateOrderStatus(selectedItem.id, { name: formData.name, isActive: formData.isActive })
            toast.success('Order status updated')
          } else {
            await referenceApi.createOrderStatus(formData.name)
            toast.success('Order status created')
          }
          fetchOrderStatuses()
          break
          
        case 'property-types':
          if (selectedItem) {
            await referenceApi.updatePropertyType(selectedItem.id, { name: formData.name, isActive: formData.isActive })
            toast.success('Property type updated')
          } else {
            await referenceApi.createPropertyType(formData.name)
            toast.success('Property type created')
          }
          fetchPropertyTypes()
          break
          
        case 'product-types':
          await referenceApi.createProductType(formData.name)
          toast.success('Product type created')
          fetchProductTypes()
          break
          
        case 'states':
          await referenceApi.createState({ code: formData.code || formData.name, name: formData.name || formData.code })
          toast.success('State created')
          fetchStates()
          break
          
        case 'duplicate-settings':
          if (selectedItem) {
            await duplicateConfigApi.update(selectedItem.id, formData.isActive)
            toast.success('Duplicate setting updated')
          } else {
            await duplicateConfigApi.create(formData.name)
            toast.success('Product type added to duplicate settings')
          }
          fetchDuplicateProducts()
          break
      }
      setEditDialogOpen(false)
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail
      if (Array.isArray(errorDetail)) {
        toast.error(errorDetail[0]?.msg || 'Failed to save')
      } else if (typeof errorDetail === 'object') {
        toast.error(errorDetail?.msg || 'Failed to save')
      } else {
        toast.error(errorDetail || 'Failed to save')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedItem) return
    
    setIsSubmitting(true)
    try {
      switch (currentType) {
        case 'fa-names':
          await faNamesApi.delete(selectedItem.id)
          toast.success('FA name deleted')
          fetchFaNames()
          break
        case 'transaction-types':
        case 'order-statuses':
          if (currentType === 'transaction-types') {
            await referenceApi.updateTransactionType(selectedItem.id, { isActive: false })
            fetchTransactionTypes()
          } else if (currentType === 'order-statuses') {
            await referenceApi.updateOrderStatus(selectedItem.id, { isActive: false })
            fetchOrderStatuses()
          }
          toast.success('Item deactivated')
          break
        case 'property-types':
        case 'product-types':
        case 'states':
          toast.error('Cannot delete - this data is used by teams. Remove from all teams first.')
          break
        case 'duplicate-settings':
          await duplicateConfigApi.delete(selectedItem.id)
          toast.success('Product type removed from duplicate settings')
          fetchDuplicateProducts()
          break
      }
      setDeleteDialogOpen(false)
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail
      if (Array.isArray(errorDetail)) {
        toast.error(errorDetail[0]?.msg || 'Failed to delete')
      } else if (typeof errorDetail === 'object') {
        toast.error(errorDetail?.msg || 'Failed to delete')
      } else {
        toast.error(errorDetail || 'Failed to delete')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderTable = (
    items: ReferenceItem[],
    loading: boolean,
    type: string,
    showCode: boolean = false,
    readOnly: boolean = false
  ) => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      )
    }

    return (
      <>
        {readOnly && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2">
            <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium">Read-only data</p>
              <p>These values are managed via Team configuration. Edit team settings to add or modify values.</p>
            </div>
          </div>
        )}
        <Table>
          <TableHeader>
            <TableRow>
              {showCode ? <TableHead>Code</TableHead> : <TableHead>Name</TableHead>}
              {!readOnly && <TableHead>Status</TableHead>}
              {!readOnly && <TableHead className="text-right">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={readOnly ? 1 : 3} className="text-center text-slate-500">
                  No items found. {readOnly ? 'Add teams with product types/states to populate this list.' : 'Click "Add New" to create one.'}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={String(item.id)}>
                  {showCode ? (
                    <TableCell className="font-medium">{String(item.code || '')}</TableCell>
                  ) : (
                    <TableCell>{String(item.name || '')}</TableCell>
                  )}
                  {!readOnly && (
                    <TableCell>
                      <Badge variant={item.isActive ? 'default' : 'secondary'}>
                        {item.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                  )}
                  {!readOnly && (
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenEdit(type, item)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDelete(type, item)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminHeader />
      <AdminNav />
      <Toaster position="top-right" />
      
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Settings className="h-6 w-6 text-slate-600" />
            <h1 className="text-2xl font-bold text-slate-900">Reference Data Management</h1>
          </div>
          <Button onClick={() => handleOpenAdd(activeTab)}>
            <Plus className="h-4 w-4 mr-2" />
            Add New
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="flex flex-wrap h-auto gap-1 mb-4">
            <TabsTrigger key="transaction-types" value="transaction-types">Transaction Types</TabsTrigger>
            <TabsTrigger key="order-statuses" value="order-statuses">Order Statuses</TabsTrigger>
            <TabsTrigger key="product-types" value="product-types">Product Types</TabsTrigger>
            <TabsTrigger key="property-types" value="property-types">Property Types</TabsTrigger>
            <TabsTrigger key="states" value="states">States</TabsTrigger>
            <TabsTrigger key="fa-names" value="fa-names">FA Names</TabsTrigger>
            <TabsTrigger key="duplicate-settings" value="duplicate-settings">Duplicate Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="transaction-types">
            <Card>
              <CardHeader>
                <CardTitle>Transaction Types</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(transactionTypes, transactionTypesLoading, 'transaction-types')}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="order-statuses">
            <Card>
              <CardHeader>
                <CardTitle>Order Statuses</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(orderStatuses, orderStatusesLoading, 'order-statuses')}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="product-types">
            <Card>
              <CardHeader>
                <CardTitle>Product Types</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(productTypes as unknown as ReferenceItem[], productTypesLoading, 'product-types', false, false)}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="property-types">
            <Card>
              <CardHeader>
                <CardTitle>Property Types</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(propertyTypes as unknown as ReferenceItem[], propertyTypesLoading, 'property-types', false, false)}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="states">
            <Card>
              <CardHeader>
                <CardTitle>States</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(states as unknown as ReferenceItem[], statesLoading, 'states', true, false)}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="fa-names">
            <Card>
              <CardHeader>
                <CardTitle>FA Names</CardTitle>
              </CardHeader>
              <CardContent>
                {renderTable(faNames as unknown as ReferenceItem[], faNamesLoading, 'fa-names')}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="duplicate-settings">
            <Card>
              <CardHeader>
                <CardTitle>Duplicate Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md flex items-start gap-2">
                  <Info className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-amber-700">
                    <p className="font-medium">Duplicate File Numbers</p>
                    <p>Product types listed here can have duplicate file numbers. Only Superadmins, Admins, and Team Leads can create duplicates for these product types.</p>
                  </div>
                </div>
                {duplicateProductsLoading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Product Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {duplicateProducts.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center text-slate-500">
                            No product types configured for duplicate file numbers. Click "Add New" to add one.
                          </TableCell>
                        </TableRow>
                      ) : (
                        duplicateProducts.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell className="font-medium">{item.productType}</TableCell>
                            <TableCell>
                              <Badge variant={item.isActive ? 'default' : 'secondary'}>
                                {item.isActive ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleOpenEdit('duplicate-settings', { id: item.id, name: item.productType, isActive: item.isActive })}
                                >
                                  <Edit2 className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleOpenDelete('duplicate-settings', { id: item.id, name: item.productType, isActive: item.isActive })}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Edit/Create Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedItem ? 'Edit' : 'Add'} {currentType.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {currentType === 'states' && (
              <div className="space-y-2">
                <Label htmlFor="code">State Code</Label>
                <Input
                  id="code"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase(), name: e.target.value.toUpperCase() })}
                  placeholder="e.g., CA, DE-ATO"
                  disabled={!!selectedItem}
                />
              </div>
            )}
            {currentType === 'duplicate-settings' && !selectedItem && (
              <div className="space-y-2">
                <Label htmlFor="name">Product Type</Label>
                <Select
                  value={formData.name}
                  onValueChange={(value) => setFormData({ ...formData, name: value })}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a product type..." />
                  </SelectTrigger>
                  <SelectContent position="popper" side="bottom" align="start">
                    {productTypes
                      .filter(pt => !duplicateProducts.some(
                        dp => dp.productType.toLowerCase() === pt.name.toLowerCase()
                      ))
                      .map(pt => (
                        <SelectItem key={pt.id} value={pt.name}>{pt.name}</SelectItem>
                      ))
                    }
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">Select a product type to allow duplicate file numbers.</p>
              </div>
            )}
            {currentType !== 'states' && currentType !== 'duplicate-settings' && (
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter name"
                />
              </div>
            )}
            {currentType !== 'states' && (currentType !== 'duplicate-settings' || selectedItem) && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={formData.isActive}
                  onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                  className="rounded"
                />
                <Label htmlFor="isActive">Active</Label>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {selectedItem ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              {currentType === 'property-types' || currentType === 'product-types' || currentType === 'states' ? (
                <>These values are managed via Team configuration. Cannot delete from here.</>
              ) : currentType === 'duplicate-settings' ? (
                <>Are you sure you want to remove "{selectedItem?.name}" from duplicate settings? Orders with this product type will no longer allow duplicate file numbers.</>
              ) : (
                <>Are you sure you want to {currentType === 'transaction-types' || currentType === 'process-types' || currentType === 'order-statuses' ? 'deactivate' : 'delete'} "{selectedItem?.name}"?
                {currentType === 'transaction-types' || currentType === 'process-types' || currentType === 'order-statuses' && ' This will set the item as inactive.'}</>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              {currentType === 'property-types' || currentType === 'product-types' || currentType === 'states' ? 'Close' : 'Cancel'}
            </Button>
            {!(currentType === 'property-types' || currentType === 'product-types' || currentType === 'states') && (
              <Button variant="destructive" onClick={handleDelete} disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {currentType === 'transaction-types' || currentType === 'process-types' || currentType === 'order-statuses' ? 'Deactivate' : 'Delete'}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ReferenceDataPage
