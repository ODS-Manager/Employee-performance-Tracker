import { useState, useEffect, useMemo, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { teamsApi, referenceApi, usersApi, ordersApi, organizationsApi } from '../../services/api'
import { getPstDateInputValue } from '../../utils/helpers'
import type { 
  FileNumberCheckResponse,
  OrderCreate, 
  OrderUpdate,
  Order
} from '../../types'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import { Loader2, Save, Info } from 'lucide-react'
import toast from 'react-hot-toast'

interface OrderFormProps {
  order?: Order
  onSuccess?: () => void
  onCancel?: () => void
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const OrderForm = ({ order, onSuccess, onCancel: _onCancel }: OrderFormProps) => {
  const isEditMode = !!order
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  // Get edit permissions from the order (set by backend)
  const editPermissions = order?.editPermissions
  const isEditLocked = isEditMode && editPermissions?.canEdit === false
  
  // Determine what this user can edit in edit mode
  // When edit is locked (e.g., billing done), all fields are read-only
  const canEditOrderDetails = !isEditLocked && (!isEditMode || (editPermissions?.canEditOrderDetails ?? true))
  const canEditStep1 = !isEditLocked && (!isEditMode || (editPermissions?.canEditStep1 ?? true))
  const canEditStep2 = !isEditLocked && (!isEditMode || (editPermissions?.canEditStep2 ?? true))
  const canEditOrderStatus = !isEditLocked && (!isEditMode || (editPermissions?.canEditOrderStatus ?? true))
  
  // Form state
  const [fileNumber, setFileNumber] = useState('')
  const [entryDate, setEntryDate] = useState(getPstDateInputValue())
  const [selectedOrgId, setSelectedOrgId] = useState<number | null>(null)
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [selectedState, setSelectedState] = useState('')
  const [county, setCounty] = useState('')
  const [selectedProductType, setSelectedProductType] = useState('')
  const [selectedProductionType, setSelectedProductionType] = useState<'regular' | 'OT'>('regular')
  const [selectedTransactionTypeId, setSelectedTransactionTypeId] = useState<number | null>(null)
  const [selectedProcessTypeId, setSelectedProcessTypeId] = useState<number | null>(null)
  const [selectedOrderStatusId, setSelectedOrderStatusId] = useState<number | null>(null)
  const [selectedDivisionId, setSelectedDivisionId] = useState<number | null>(null)
  const [selectedPropertyTypeId, setSelectedPropertyTypeId] = useState<number | null>(null)
  
  // Step assignment state - only used by admins
  const [step1UserId, setStep1UserId] = useState<number | null>(null)
  const [step1FaNameId, setStep1FaNameId] = useState<number | null>(null)
  const [step2UserId, setStep2UserId] = useState<number | null>(null)
  const [step2FaNameId, setStep2FaNameId] = useState<number | null>(null)
  
  const [submitting, setSubmitting] = useState(false)
  
  // File number check state - simplified
  const [fileNumberExists, setFileNumberExists] = useState(false)
  const [canAddStep2, setCanAddStep2] = useState(false)
  const [canAddStep1, setCanAddStep1] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_existingOrderId, setExistingOrderId] = useState<number | null>(null)
  const [isCheckingFileNumber, setIsCheckingFileNumber] = useState(false)
  const [isDuplicateEntry, setIsDuplicateEntry] = useState(false)
  const [selectedDuplicateAssigneeId, setSelectedDuplicateAssigneeId] = useState<number | null>(null)
  const [duplicateChoiceOpen, setDuplicateChoiceOpen] = useState(false)
  const [pendingDuplicateCheck, setPendingDuplicateCheck] = useState<FileNumberCheckResponse | null>(null)

  // Check user role - determines form behavior
  const isAdminOrSuperadmin = user?.userRole === 'admin' || user?.userRole === 'superadmin'
  const isTeamLead = user?.userRole === 'team_lead'
  // const isEmployee = user?.userRole === 'examiner'
  
  // Can this user assign work to others? (admin, superadmin, team_lead)
  const canAssignToOthers = isAdminOrSuperadmin || isTeamLead
  const canEditEntryDate = canEditOrderDetails && (isAdminOrSuperadmin || isTeamLead)
  const [disableCreateAutoDefaults, setDisableCreateAutoDefaults] = useState(false)

  const resetCreateForm = () => {
    setDisableCreateAutoDefaults(true)
    setSelectedOrgId(null)
    setSelectedTeamId(null)
    setFileNumber('')
    setEntryDate(getPstDateInputValue())
    setSelectedState('')
    setCounty('')
    setSelectedProductType('')
    setSelectedProductionType('regular')
    setSelectedTransactionTypeId(null)
    setSelectedProcessTypeId(null)
    const completedStatus = orderStatuses?.find(s => s.isActive && s.name.toLowerCase() === 'completed')
    setSelectedOrderStatusId(completedStatus?.id || null)
    setSelectedDivisionId(null)
    setSelectedPropertyTypeId(null)
    setStep1UserId(null)
    setStep2UserId(null)
    setStep1FaNameId(null)
    setStep2FaNameId(null)
    setFileNumberExists(false)
    setCanAddStep2(false)
    setCanAddStep1(false)
    setExistingOrderId(null)
    setIsDuplicateEntry(false)
    setSelectedDuplicateAssigneeId(null)
    setDuplicateChoiceOpen(false)
    setPendingDuplicateCheck(null)
  }

  // For regular users: fetch their team memberships
  const { data: userProfile, isLoading: loadingUserProfile } = useQuery({
    queryKey: ['userProfile', user?.id],
    queryFn: () => usersApi.get(user!.id),
    enabled: !!user && !isAdminOrSuperadmin,
  })

  // For superadmin: fetch all organizations to allow selection
  const { data: organizationsData, isLoading: loadingOrganizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.list({ isActive: true }),
    enabled: !!user && user.userRole === 'superadmin',
  })

  // Determine which orgId to use for fetching teams
  const effectiveOrgId = user?.userRole === 'superadmin' 
    ? selectedOrgId 
    : (user?.orgId || null)

  // For admin/superadmin: fetch all teams in the selected organization
  const { data: allTeamsData, isLoading: loadingAllTeams } = useQuery({
    queryKey: ['teams', effectiveOrgId],
    queryFn: () => teamsApi.list({ orgId: effectiveOrgId || undefined, isActive: true }),
    enabled: !!user && isAdminOrSuperadmin && !!effectiveOrgId,
  })

  // Fetch team details when a team is selected (moved up to be available in getAvailableTeams)
  const { data: selectedTeamDetails, isLoading: loadingTeamDetails } = useQuery({
    queryKey: ['team', selectedTeamId],
    queryFn: () => teamsApi.get(selectedTeamId!),
    enabled: !!selectedTeamId,
  })

  // Get the teams to display based on user role
  const getAvailableTeams = (): { id: number; name: string }[] => {
    let teams: { id: number; name: string }[] = []
    
    if (isAdminOrSuperadmin) {
      // Admin/Superadmin sees all org teams
      teams = allTeamsData?.items?.map(t => ({ id: t.id, name: t.name })) || []
    } else {
      // Regular users (employee, team_lead) only see their assigned teams
      // Filter by both: user's membership active (isActive) AND team not deactivated (teamIsActive)
      teams = userProfile?.teams?.filter(t => t.isActive && t.teamIsActive).map(t => ({ 
        id: t.teamId, 
        name: t.teamName 
      })) || []
    }
    
    // In edit mode, ensure the order's team is always in the list
    if (isEditMode && order?.teamId) {
      const orderTeamExists = teams.some(t => t.id === order.teamId)
      if (!orderTeamExists) {
        // Use the team name from selectedTeamDetails if available, otherwise show placeholder
        const teamName = selectedTeamDetails?.name || `Team ${order.teamId}`
        teams = [{ id: order.teamId, name: teamName }, ...teams]
      }
    }
    
    return teams
  }

  const availableTeams = getAvailableTeams()
  const loadingTeams = isAdminOrSuperadmin ? (loadingAllTeams || loadingOrganizations) : loadingUserProfile

  // Fetch reference data
  const { data: transactionTypes, isLoading: loadingTransactionTypes } = useQuery({
    queryKey: ['transactionTypes'],
    queryFn: referenceApi.getTransactionTypes,
  })

  const { data: processTypes, isLoading: loadingProcessTypes } = useQuery({
    queryKey: ['processTypes'],
    queryFn: referenceApi.getProcessTypes,
  })

  const { data: orderStatuses, isLoading: loadingOrderStatuses } = useQuery({
    queryKey: ['orderStatuses'],
    queryFn: referenceApi.getOrderStatuses,
  })

  const { data: divisions, isLoading: loadingDivisions } = useQuery({
    queryKey: ['divisions'],
    queryFn: referenceApi.getDivisions,
  })

  const { data: propertyTypes, isLoading: loadingPropertyTypes } = useQuery({
    queryKey: ['propertyTypes'],
    queryFn: referenceApi.getPropertyTypes,
  })

  // Fetch all team members for step user assignment (admin/team lead)
  const { data: teamMembersData, isLoading: loadingTeamMembers } = useQuery({
    queryKey: ['teamMembers', selectedTeamId],
    queryFn: () => usersApi.list({ teamId: selectedTeamId!, isActive: true }),
    enabled: !!selectedTeamId && canAssignToOthers,
  })

  const teamMemberOptions = useMemo(() => {
    const members = (teamMembersData?.items || []).map((u) => ({
      id: u.id,
      label: u.userName,
    }))

    if (!user) {
      return members
    }

    const withYouLabel = members.map((opt) => (
      opt.id === user.id ? { ...opt, label: `${opt.label} (You)` } : opt
    ))

    if (!withYouLabel.some((opt) => opt.id === user.id)) {
      return [{ id: user.id, label: `${user.userName} (You)` }, ...withYouLabel]
    }

    return withYouLabel
  }, [teamMembersData?.items, user])

  // Fetch FA names pool for the selected team - for order masking
  const { data: faNamesData, isLoading: loadingFaNames } = useQuery({
    queryKey: ['teamFaNames', selectedTeamId],
    queryFn: () => teamsApi.getFaNames(selectedTeamId!),
    enabled: !!selectedTeamId,
  })
  const faNames = faNamesData?.items || []

  // Get available states and products from selected team
  // In edit mode, ensure the order's current values are always included in the options
  const teamStates = selectedTeamDetails?.states?.map(s => s.state) || []
  const teamProducts = selectedTeamDetails?.products?.map(p => p.productType) || []
  
  // Include the order's current state/product if not already in the list (for edit mode)
  const availableStates = isEditMode && order?.state && !teamStates.includes(order.state)
    ? [order.state, ...teamStates]
    : teamStates
  const availableProducts = isEditMode && order?.productType && !teamProducts.includes(order.productType)
    ? [order.productType, ...teamProducts]
    : teamProducts

  const clearDuplicateChoice = useCallback(() => {
    setDuplicateChoiceOpen(false)
    setPendingDuplicateCheck(null)
  }, [])

  const applyExistingOrderChoice = (result: FileNumberCheckResponse) => {
    clearDuplicateChoice()
    setIsDuplicateEntry(false)
    setSelectedDuplicateAssigneeId(null)

    if (result.sameTeam && result.step1Completed && !result.step2Completed) {
      setFileNumberExists(true)
      setCanAddStep2(true)
      setCanAddStep1(false)
      setExistingOrderId(result.orderId)

      if (result.existingOrderDetails) {
        const details = result.existingOrderDetails
        setSelectedState(details.state || '')
        setCounty(details.county || '')
        setSelectedProductionType(details.productionType || 'regular')
        setSelectedTransactionTypeId(details.transactionTypeId || null)
        setSelectedOrderStatusId(details.orderStatusId || null)
        setSelectedDivisionId(details.divisionId || null)
        setSelectedPropertyTypeId(details.propertyTypeId || null)
        if (details.entryDate) {
          setEntryDate(details.entryDate)
        }
      }

      const step2Process = processTypes?.find(p => p.name === 'Step2' && p.isActive)
      if (step2Process) {
        setSelectedProcessTypeId(step2Process.id)
      }

      toast.success('Existing file selected. Add Step 2 to update it.', { duration: 5000 })
      return
    }

    if (result.sameTeam && !result.step1Completed && result.step2Completed) {
      setFileNumberExists(true)
      setCanAddStep2(false)
      setCanAddStep1(true)
      setExistingOrderId(result.orderId)

      if (result.existingOrderDetails) {
        const details = result.existingOrderDetails
        setSelectedState(details.state || '')
        setCounty(details.county || '')
        setSelectedProductionType(details.productionType || 'regular')
        setSelectedTransactionTypeId(details.transactionTypeId || null)
        setSelectedOrderStatusId(details.orderStatusId || null)
        setSelectedDivisionId(details.divisionId || null)
        setSelectedPropertyTypeId(details.propertyTypeId || null)
        if (details.entryDate) {
          setEntryDate(details.entryDate)
        }
      }

      const step1Process = processTypes?.find(p => p.name === 'Step1' && p.isActive)
      if (step1Process) {
        setSelectedProcessTypeId(step1Process.id)
      }

      toast.success('Existing file selected. Add Step 1 to update it.', { duration: 5000 })
      return
    }

    setFileNumberExists(true)
    setCanAddStep2(false)
    setCanAddStep1(false)
    setExistingOrderId(result.orderId)

    if (result.orderId) {
      navigate(`/examiner/edit-order/${result.orderId}`)
    } else {
      toast.error('File number with this product type already exists', { duration: 5000 })
    }
  }

  const applyDuplicateEntryChoice = () => {
    clearDuplicateChoice()
    setFileNumberExists(false)
    setCanAddStep2(false)
    setCanAddStep1(false)
    setExistingOrderId(null)
    setIsDuplicateEntry(true)
    setSelectedDuplicateAssigneeId(null)
    toast.success('Duplicate entry selected.', { duration: 4000 })
  }

  // Check file number + product type combination - check if it exists globally
  const checkFileNumberAndProduct = async (fileNum: string, productType: string) => {
    if (!fileNum.trim() || !productType.trim() || !selectedTeamId || isEditMode) {
      setFileNumberExists(false)
      setCanAddStep2(false)
      setCanAddStep1(false)
      setExistingOrderId(null)
      setIsDuplicateEntry(false)
      setSelectedDuplicateAssigneeId(null)
      clearDuplicateChoice()
      return
    }
    
    setIsCheckingFileNumber(true)
    try {
      const result = await ordersApi.checkFileNumber(fileNum.trim(), selectedTeamId, productType.trim())
      const duplicateEntryAllowed = !!result.duplicatesAllowed

      if (result.exists) {
        if (duplicateEntryAllowed) {
          setFileNumberExists(true)
          setCanAddStep2(false)
          setCanAddStep1(false)
          setExistingOrderId(result.orderId)
          setIsDuplicateEntry(false)
          setSelectedDuplicateAssigneeId(null)
          setPendingDuplicateCheck(result)
          setDuplicateChoiceOpen(true)
        } else {
          applyExistingOrderChoice(result)
        }
      } else {
        // File + product combination doesn't exist anywhere - new order allowed
        setFileNumberExists(false)
        setCanAddStep2(false)
        setCanAddStep1(false)
        setIsDuplicateEntry(duplicateEntryAllowed)
        if (!duplicateEntryAllowed) {
          setSelectedDuplicateAssigneeId(null)
        }
        setExistingOrderId(null)
        clearDuplicateChoice()
      }
    } catch (error) {
      console.error('Error checking file number:', error)
      setFileNumberExists(false)
      setCanAddStep2(false)
      setCanAddStep1(false)
      setExistingOrderId(null)
      setIsDuplicateEntry(false)
      setSelectedDuplicateAssigneeId(null)
      clearDuplicateChoice()
    } finally {
      setIsCheckingFileNumber(false)
    }
  }

  // Check file number on blur - requires both file number and product type
  const handleFileNumberBlur = async () => {
    await checkFileNumberAndProduct(fileNumber, selectedProductType)
  }

  // Check when product type changes (if file number is already filled)
  const handleProductTypeChange = async (newProductType: string) => {
    setSelectedProductType(newProductType)
    // Reset the check states when product type changes
    setFileNumberExists(false)
    setCanAddStep2(false)
    setCanAddStep1(false)
    setExistingOrderId(null)
    setIsDuplicateEntry(false)
    setSelectedDuplicateAssigneeId(null)
    clearDuplicateChoice()
    // Check if file number is already filled
    if (fileNumber.trim() && newProductType.trim() && selectedTeamId && !isEditMode) {
      await checkFileNumberAndProduct(fileNumber, newProductType)
    }
  }

  // Reset dependent fields when team changes (only in create mode)
  useEffect(() => {
    if (!isEditMode) {
      // Reset fields first
      setSelectedState('')
      setSelectedProductType('')
      setCounty('')
      setSelectedTransactionTypeId(null)
      setStep1UserId(null)
      setStep2UserId(null)
      setStep1FaNameId(null)
      setStep2FaNameId(null)
      setFileNumberExists(false)
      setCanAddStep2(false)
      setCanAddStep1(false)
      setExistingOrderId(null)
      setIsDuplicateEntry(false)
      setSelectedDuplicateAssigneeId(null)
      clearDuplicateChoice()
    }
  }, [selectedTeamId, isEditMode, clearDuplicateChoice])

  // Auto-select organization for admin users (they have a fixed orgId)
  useEffect(() => {
    if (!isEditMode && !disableCreateAutoDefaults && user?.userRole === 'admin' && user.orgId && !selectedOrgId) {
      setSelectedOrgId(user.orgId)
    }
  }, [user, selectedOrgId, isEditMode, disableCreateAutoDefaults])

  // Reset team selection when organization changes
  useEffect(() => {
    if (!isEditMode) {
      setSelectedTeamId(null)
    }
  }, [selectedOrgId, isEditMode])

  // Initialize form with order data in edit mode
  useEffect(() => {
    if (isEditMode && order) {
      setFileNumber(order.fileNumber)
      setEntryDate(order.entryDate.split('T')[0])
      setSelectedOrgId(order.orgId) // Set organization ID in edit mode
      setSelectedTeamId(order.teamId)
      setSelectedState(order.state)
      setCounty(order.county)
      setSelectedProductType(order.productType)
      setSelectedProductionType(order.productionType || 'regular')
      setSelectedTransactionTypeId(order.transactionTypeId)
      setSelectedProcessTypeId(order.processTypeId)
      setSelectedOrderStatusId(order.orderStatusId)
      setSelectedDivisionId(order.divisionId)
      setSelectedPropertyTypeId(order.propertyTypeId || null)
      
      // Set step info
      if (order.step1) {
        if (order.step1.userId) setStep1UserId(order.step1.userId)
        if (order.step1.faNameId) setStep1FaNameId(order.step1.faNameId)
      }
      if (order.step2) {
        if (order.step2.userId) setStep2UserId(order.step2.userId)
        if (order.step2.faNameId) setStep2FaNameId(order.step2.faNameId)
      }
    }
  }, [isEditMode, order])

  // Auto-select team if user only has one team (only in create mode)
  useEffect(() => {
    if (!isEditMode && !disableCreateAutoDefaults && availableTeams.length === 1 && !selectedTeamId) {
      setSelectedTeamId(availableTeams[0].id)
    }
  }, [availableTeams, selectedTeamId, isEditMode, disableCreateAutoDefaults])

  // Auto-set order status to Completed when available (only in create mode)
  useEffect(() => {
    if (!isEditMode && !disableCreateAutoDefaults && orderStatuses?.length && !selectedOrderStatusId) {
      const activeStatuses = orderStatuses.filter(s => s.isActive)
      const completedStatus = activeStatuses.find(s => s.name.toLowerCase() === 'completed')
      const defaultStatus = completedStatus || activeStatuses[0]
      if (defaultStatus) setSelectedOrderStatusId(defaultStatus.id)
    }
  }, [orderStatuses, selectedOrderStatusId, isEditMode, disableCreateAutoDefaults])

  // Auto-set division to first one (only in create mode)
  useEffect(() => {
    if (!isEditMode && !disableCreateAutoDefaults && divisions?.length && !selectedDivisionId) {
      setSelectedDivisionId(divisions[0].id)
    }
  }, [divisions, selectedDivisionId, isEditMode, disableCreateAutoDefaults])

  // Auto-set process type for examiners (only in create mode)
  useEffect(() => {
    if (!isEditMode && !disableCreateAutoDefaults && processTypes?.length && !selectedProcessTypeId) {
      // Default to first active process type
      const defaultProcess = processTypes.find(p => p.isActive)
      if (defaultProcess) setSelectedProcessTypeId(defaultProcess.id)
    }
  }, [processTypes, selectedProcessTypeId, isEditMode, disableCreateAutoDefaults])

  // Handle process type changes - manage step users for Single Seat
  useEffect(() => {
    const selectedProcessType = processTypes?.find(p => p.id === selectedProcessTypeId)
    if (selectedProcessType?.name === 'Single Seat' && canAssignToOthers) {
      // For single seat, step2 user should be same as step1
      setStep2UserId(step1UserId)
    }
  }, [selectedProcessTypeId, step1UserId, processTypes, canAssignToOthers])

  const validateForm = (): boolean => {
    const newErrors: string[] = []
    
    // Superadmin must select an organization
    if (user?.userRole === 'superadmin' && !selectedOrgId) {
      newErrors.push('Center is required')
    }
    
    if (!fileNumber.trim()) newErrors.push('File number is required')
    if (!entryDate) newErrors.push('Entry date is required')
    if (!selectedTeamId) newErrors.push('Team is required')
    if (!selectedState) newErrors.push('State is required')
    if (!county.trim()) newErrors.push('County is required')
    if (!selectedProductType) newErrors.push('Product type is required')
    if (!selectedTransactionTypeId) newErrors.push('Transaction type is required')
    if (!selectedProcessTypeId) newErrors.push('Process type is required')
    if (!selectedDivisionId) newErrors.push('Division is required')
    if (!selectedPropertyTypeId) newErrors.push('Property type is required')
    if (!selectedProductionType) newErrors.push('Production type is required')
    
    // Order status is required for admins, and also for examiners who can edit order details or order status
    if ((canAssignToOthers || canEditOrderDetails || canEditOrderStatus) && !selectedOrderStatusId) newErrors.push('Order status is required')
    if (!isEditMode && canAssignToOthers && isDuplicateEntry && !selectedDuplicateAssigneeId) {
      newErrors.push('Examiner is required for duplicate order entry')
    }
    
    // Validate step user assignment for admin/team lead (mandatory)
    if (canAssignToOthers && !isDuplicateEntry) {
      const currentPT = processTypes?.find(p => p.id === selectedProcessTypeId)
      if (currentPT?.name === 'Step1' || currentPT?.name === 'Single Seat') {
        if (!step1UserId) newErrors.push('Assign To user is required for Step 1')
      }
      if (currentPT?.name === 'Step2') {
        if (!step2UserId) newErrors.push('Assign To user is required for Step 2')
      }
    }
    
    // NOTE: We don't validate duplicate file numbers on the frontend anymore.
    // The backend will return appropriate error messages as toast notifications.
    
    // Validate FA names and dates are required
    const currentProcessType = processTypes?.find(p => p.id === selectedProcessTypeId)
    if (currentProcessType) {
      // Validate FA names first
      if (isEditMode && !canAssignToOthers) {
        // Employee editing - validate FA names for steps they can edit
        if (canEditStep1) {
          if (!step1FaNameId) {
            newErrors.push('Step 1 FA name is required')
          }
        }
        if (canEditStep2) {
          if (currentProcessType.name === 'Single Seat') {
            if (!step1FaNameId) {
              newErrors.push('Step 1 FA name is required')
            }
          } else if (!step2FaNameId) {
            newErrors.push('Step 2 FA name is required')
          }
        }
      } else {
        // Create mode or admin - validate FA names based on process type
        if (currentProcessType.name === 'Step1' || currentProcessType.name === 'Single Seat') {
          if (!step1FaNameId) {
            newErrors.push('Step 1 FA name is required')
          }
        }
        if (currentProcessType.name === 'Step2') {
          if (!step2FaNameId) {
            newErrors.push('Step 2 FA name is required')
          }
        }
      }
      
      // Date validation removed - dates are optional and validated by backend if needed
    }
    
    // Show validation errors as toast notifications
    if (newErrors.length > 0) {
      toast.error(newErrors.join('\n'))
    }
    
    return newErrors.length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Prevent submission when editing is locked (e.g., billing done)
    if (isEditLocked) {
      toast.error('This order cannot be edited — ' + (editPermissions?.reason || 'editing is locked'))
      return
    }
    
    if (!validateForm()) return
    
    setSubmitting(true)
    
    try {
      const selectedProcessType = processTypes?.find(p => p.id === selectedProcessTypeId)
      let duplicateEntryForSubmit = isDuplicateEntry

      const usingExistingPartialOrder = fileNumberExists && (canAddStep1 || canAddStep2)

      if (!isEditMode && canAssignToOthers && !usingExistingPartialOrder && selectedTeamId && selectedProductType.trim() && fileNumber.trim()) {
        const checkResult = await ordersApi.checkFileNumber(fileNumber.trim(), selectedTeamId, selectedProductType.trim())
        duplicateEntryForSubmit = isDuplicateEntry || (!!checkResult.duplicatesAllowed && !checkResult.exists)
        setIsDuplicateEntry(duplicateEntryForSubmit)
        if (!duplicateEntryForSubmit) {
          setSelectedDuplicateAssigneeId(null)
        }
      }

      if (!isEditMode && canAssignToOthers && duplicateEntryForSubmit && !selectedDuplicateAssigneeId) {
        toast.error('Select an examiner for duplicate order entry')
        return
      }
      
      // For examiners editing existing orders, only send step-related fields
      // This prevents sending order details that they can't modify
      const isEmployeeEditingExisting = isEditMode && order && !canAssignToOthers
      
      let orderData: OrderCreate | OrderUpdate
      
      if (isEmployeeEditingExisting) {
        // Employee editing existing order
        if (canEditOrderDetails) {
          // Sole Single Seat examiner — can edit everything, send all fields like admin
          orderData = {
            fileNumber: fileNumber.trim(),
            transactionTypeId: selectedTransactionTypeId!,
            processTypeId: selectedProcessTypeId!,
            orderStatusId: selectedOrderStatusId!,
            divisionId: selectedDivisionId!,
            propertyTypeId: selectedPropertyTypeId || undefined,
            state: selectedState,
            county: county.trim(),
            productType: selectedProductType,
            productionType: selectedProductionType,
            teamId: selectedTeamId!,
            orgId: effectiveOrgId || user?.orgId || 0,
          }
          // Also set step fields — mirror step1FaNameId to step2FaNameId for Single Seat
          if (canEditStep1) {
            orderData.step1UserId = user!.id
            if (step1FaNameId) {
              orderData.step1FaNameId = step1FaNameId
              orderData.step2FaNameId = step1FaNameId  // Single Seat: same FA name for both
            }
          }
          if (canEditStep2) {
            orderData.step2UserId = user!.id
          }
        } else {
          // Shared Single Seat or Step1/Step2 — only send step fields they CAN edit
          orderData = {} as OrderUpdate

          // Send order status if employee can update it (e.g., marking as completed)
          if (canEditOrderStatus && selectedOrderStatusId) {
            orderData.orderStatusId = selectedOrderStatusId
          }

          // Send Step 1 data if employee can edit it
          if (canEditStep1) {
            orderData.step1UserId = user!.id
            if (step1FaNameId) orderData.step1FaNameId = step1FaNameId
          }

          // Send Step 2 data if employee can edit it
          if (canEditStep2) {
            orderData.step2UserId = user!.id
            // Single Seat uses step1FaNameId for both steps (same FA Name picker)
            if (selectedProcessType?.name === 'Single Seat') {
              if (step1FaNameId) orderData.step2FaNameId = step1FaNameId
            } else {
              if (step2FaNameId) orderData.step2FaNameId = step2FaNameId
            }
          }
        }
      } else {
        // Admin/Team Lead OR new order creation - send all fields
        orderData = {
          fileNumber: fileNumber.trim(),
          transactionTypeId: selectedTransactionTypeId!,
          processTypeId: selectedProcessTypeId!,
          orderStatusId: selectedOrderStatusId!,
          divisionId: selectedDivisionId!,
          propertyTypeId: selectedPropertyTypeId || undefined,
          state: selectedState,
          county: county.trim(),
          productType: selectedProductType,
          productionType: selectedProductionType,
          teamId: selectedTeamId!,
          orgId: effectiveOrgId || user?.orgId || 0,
        }

        if (!isEditMode && duplicateEntryForSubmit) {
          orderData.forceDuplicate = true
        }

        // Entry date is editable on edit page for admins/superadmins/team leads.
        // For create mode, keep sending entry date (auto-generated default).
        if (!isEditMode || canEditEntryDate) {
          orderData.entryDate = entryDate
        }
        
        // Determine step user assignment
        if (canAssignToOthers) {
          if (isEditMode && order) {
            // Admin/Team Lead EDITING existing order — use step user IDs from form state (editable via dropdown)
            if (selectedProcessType?.name === 'Step1') {
              if (step1UserId) orderData.step1UserId = step1UserId
              if (step1FaNameId) orderData.step1FaNameId = step1FaNameId
            }
            
            if (selectedProcessType?.name === 'Step2') {
              if (step2UserId) orderData.step2UserId = step2UserId
              if (step2FaNameId) orderData.step2FaNameId = step2FaNameId
            }
            
            if (selectedProcessType?.name === 'Single Seat') {
              if (step1UserId) orderData.step1UserId = step1UserId
              if (step2UserId) orderData.step2UserId = step2UserId
              if (step1FaNameId) {
                orderData.step1FaNameId = step1FaNameId
                orderData.step2FaNameId = step1FaNameId
              }
            }
          } else {
            // Admin/Team Lead CREATING new order
            if (duplicateEntryForSubmit) {
              // Duplicate entry — use the duplicate assignee dropdown
              const assignedUserId = selectedDuplicateAssigneeId!
              if (selectedProcessType?.name === 'Step1') {
                orderData.step1UserId = assignedUserId
                if (step1FaNameId) orderData.step1FaNameId = step1FaNameId
              }
              if (selectedProcessType?.name === 'Step2') {
                orderData.step2UserId = assignedUserId
                if (step2FaNameId) orderData.step2FaNameId = step2FaNameId
              }
              if (selectedProcessType?.name === 'Single Seat') {
                orderData.step1UserId = assignedUserId
                orderData.step2UserId = assignedUserId
                if (step1FaNameId) {
                  orderData.step1FaNameId = step1FaNameId
                  orderData.step2FaNameId = step1FaNameId
                }
              }
            } else {
              // Normal new order — use step user IDs from dropdown (mandatory)
              if (selectedProcessType?.name === 'Step1') {
                orderData.step1UserId = step1UserId!
                if (step1FaNameId) orderData.step1FaNameId = step1FaNameId
              }
              if (selectedProcessType?.name === 'Step2') {
                orderData.step2UserId = step2UserId!
                if (step2FaNameId) orderData.step2FaNameId = step2FaNameId
              }
              if (selectedProcessType?.name === 'Single Seat') {
                orderData.step1UserId = step1UserId!
                orderData.step2UserId = step1UserId!
                if (step1FaNameId) {
                  orderData.step1FaNameId = step1FaNameId
                  orderData.step2FaNameId = step1FaNameId
                }
              }
            }
          }
        } else {
          // Employee entering their own work (new order) - auto-assign to themselves
          if (selectedProcessType?.name === 'Step1') {
            orderData.step1UserId = user!.id
            if (step1FaNameId) orderData.step1FaNameId = step1FaNameId
          }
          
          if (selectedProcessType?.name === 'Step2') {
            orderData.step2UserId = user!.id
            if (step2FaNameId) orderData.step2FaNameId = step2FaNameId
          }
          
          if (selectedProcessType?.name === 'Single Seat') {
            // Single seat - assign both steps to themselves
            orderData.step1UserId = user!.id
            orderData.step2UserId = user!.id
            if (step1FaNameId) {
              orderData.step1FaNameId = step1FaNameId
              orderData.step2FaNameId = step1FaNameId
            }
          }
        }
      }
      
      if (isEditMode && order) {
        // Update existing order
        await ordersApi.update(order.id, orderData as OrderUpdate)
        
        // Invalidate relevant caches to ensure fresh data is displayed
        await queryClient.invalidateQueries({ queryKey: ['order', order.id.toString()] })
        await queryClient.invalidateQueries({ queryKey: ['orders'] })
        
        toast.success('Order updated successfully!')
      } else {
        // Create new order (or update existing if adding Step 1 or Step 2)
        await ordersApi.create(orderData as OrderCreate)
        await queryClient.invalidateQueries({ queryKey: ['orders'] })
        
        // Show appropriate message
        if (fileNumberExists && canAddStep2) {
          toast.success('Step 2 added to existing order!')
        } else if (fileNumberExists && canAddStep1) {
          toast.success('Step 1 added to existing order!')
        } else {
          toast.success('Order created successfully!')
        }

        // Keep the form truly blank for the next entry.
        resetCreateForm()
      }
      
      onSuccess?.()
    } catch (error: any) {
      console.error('Order submission error:', error)
      console.error('Error response:', error.response)
      console.error('Error response data:', error.response?.data)
      
      let errorMsg = isEditMode ? 'Failed to update order' : 'Failed to create order'
      
      // Field name to user-friendly label mapping
      const fieldLabels: Record<string, string> = {
        'file_number': 'File Number',
        'fileNumber': 'File Number',
        'entry_date': 'Entry Date',
        'entryDate': 'Entry Date',
        'state': 'State (use 2-5 letter code like CA, TX)',
        'county': 'County',
        'product_type': 'Product Type',
        'productType': 'Product Type',
        'production_type': 'Production Type',
        'productionType': 'Production Type',
        'transaction_type_id': 'Transaction Type',
        'transactionTypeId': 'Transaction Type',
        'process_type_id': 'Process Type',
        'processTypeId': 'Process Type',
        'order_status_id': 'Order Status',
        'orderStatusId': 'Order Status',
        'division_id': 'Division',
        'divisionId': 'Division',
        'team_id': 'Team',
        'teamId': 'Team',
        'step1_start_time': 'Step 1 Start Time',
        'step1_end_time': 'Step 1 End Time',
        'step2_start_time': 'Step 2 Start Time',
        'step2_end_time': 'Step 2 End Time',
      }
      
      // Try to extract error message from various response formats
      if (error.response) {
        // Server responded with an error status
        const data = error.response.data
        console.log('Response data type:', typeof data, data)
        
        if (data) {
          if (typeof data.detail === 'string') {
            errorMsg = data.detail
          } else if (Array.isArray(data.detail)) {
            // Pydantic validation errors come as array
            const errorMessages = data.detail.map((err: any) => {
              // Extract field name from loc array (e.g., ["body", "state"] -> "state")
              const fieldName = err.loc?.slice(-1)[0] || ''
              const friendlyFieldName = fieldLabels[fieldName] || fieldName
              const message = err.msg || err.message || 'Invalid value'
              
              if (friendlyFieldName) {
                return `${friendlyFieldName}: ${message}`
              }
              return message
            })
            errorMsg = errorMessages.join('\n')
          } else if (typeof data.message === 'string') {
            errorMsg = data.message
          } else if (typeof data.error === 'string') {
            errorMsg = data.error
          } else if (typeof data === 'string') {
            errorMsg = data
          }
        }
      } else if (error.request) {
        // Request was made but no response received (network error, CORS, server down)
        errorMsg = 'Unable to reach the server. Please check your connection and try again.'
      } else if (error.message) {
        // Something else happened while setting up the request
        errorMsg = error.message
      }
      
      // Show error as toast notification
      toast.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const isLoading = loadingTeams || loadingTransactionTypes || loadingProcessTypes || loadingOrderStatuses || loadingDivisions

  const selectedProcessType = processTypes?.find(p => p.id === selectedProcessTypeId)
  const showStep1Fields = selectedProcessType?.name === 'Step1' || selectedProcessType?.name === 'Single Seat'
  const showStep2Fields = selectedProcessType?.name === 'Step2' || selectedProcessType?.name === 'Single Seat'
  
  // In edit mode, also show step fields based on edit permissions (e.g., employee adding Step 2 to Step1 order)
  const showStep1Section = showStep1Fields || (isEditMode && canEditStep1)
  const showStep2Section = showStep2Fields || (isEditMode && canEditStep2)
  
  // Disable other fields until team is selected (for new orders)
  const teamNotSelected = !isEditMode && !selectedTeamId

  // Filter process types - if file exists and can add Step 2 or Step 1, only show that type
  const availableProcessTypes = useMemo(() => {
    if (!processTypes) return []
    
    const activeTypes = processTypes.filter(p => p.isActive !== false)
    
    // In edit mode, show all active types
    if (isEditMode) {
      return activeTypes
    }
    
    // If file exists and can add Step 2, only show Step2
    if (fileNumberExists && canAddStep2) {
      return activeTypes.filter(p => p.name === 'Step2')
    }
    
    // If file exists and can add Step 1, only show Step1
    if (fileNumberExists && canAddStep1) {
      return activeTypes.filter(p => p.name === 'Step1')
    }
    
    // Otherwise show all active types
    return activeTypes
  }, [processTypes, fileNumberExists, canAddStep2, canAddStep1, isEditMode])

  // Check if form is valid for save button
  const isFormValid = useMemo(() => {
    // Basic required fields
    if (!selectedTeamId) return false
    if (duplicateChoiceOpen || pendingDuplicateCheck) return false
    if (!fileNumber.trim()) return false
    if (!entryDate) return false
    if (!selectedState) return false
    if (!county.trim()) return false
    if (!selectedProductType) return false
    if (!selectedTransactionTypeId) return false
    if (!selectedProcessTypeId) return false
    if (!selectedDivisionId) return false
    
    // Block if file exists but can't add Step 1 or Step 2
    if (!isEditMode && fileNumberExists && !canAddStep2 && !canAddStep1) return false
    
    // Superadmin must select an organization
    if (user?.userRole === 'superadmin' && !selectedOrgId) return false
    
    // Order status is required for all users
    if (!selectedOrderStatusId) return false
    if (!isEditMode && canAssignToOthers && isDuplicateEntry && !selectedDuplicateAssigneeId) return false
    
    const currentProcessType = processTypes?.find(p => p.id === selectedProcessTypeId)
    
    // Step user assignment is mandatory for admin/team lead
    if (canAssignToOthers && !isDuplicateEntry) {
      if (currentProcessType?.name === 'Step1' || currentProcessType?.name === 'Single Seat') {
        if (!step1UserId) return false
      }
      if (currentProcessType?.name === 'Step2') {
        if (!step2UserId) return false
      }
    }
    
    // Step validation based on process type and user role
    if (isEditMode && !canAssignToOthers) {
      // Examiner editing - validate based on edit permissions
      if (canEditStep1) {
        if (!step1FaNameId) return false
      }
      if (canEditStep2) {
        if (currentProcessType?.name === 'Single Seat') {
          if (!step1FaNameId) return false
        } else if (!step2FaNameId) {
          return false
        }
      }
    } else {
      // Create mode or admin - validate based on process type
      if (currentProcessType?.name === 'Step1' || currentProcessType?.name === 'Single Seat') {
        if (!step1FaNameId) return false
      }
      
      if (currentProcessType?.name === 'Step2') {
        if (!step2FaNameId) return false
      }
    }
    
    return true
  }, [
    selectedTeamId, fileNumber, entryDate, selectedState, county, selectedProductType,
    selectedTransactionTypeId, selectedProcessTypeId, selectedOrderStatusId, selectedDivisionId,
    processTypes, user?.userRole, isEditMode, canEditStep1, canEditStep2,
    fileNumberExists, canAddStep2, canAddStep1, selectedOrgId, canAssignToOthers,
    step1FaNameId, step2FaNameId, step1UserId, step2UserId, isDuplicateEntry, selectedDuplicateAssigneeId,
    duplicateChoiceOpen, pendingDuplicateCheck
  ])

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col">
      {isLoading ? (
        <Card className="h-full flex items-center justify-center border-gray-200">
          <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
        </Card>
      ) : (
        <form onSubmit={handleSubmit} className="h-full flex flex-col">
          {/* Main Content - Two Column Layout */}
          <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden min-h-0">
            
            {/* LEFT COLUMN: Order Details */}
            <div className="border border-gray-200 rounded-md p-4 bg-white flex flex-col shadow-sm overflow-hidden">
              <h3 className="text-sm font-semibold border-b border-gray-200 pb-2 mb-4 text-gray-800">Order Details</h3>
              
              <div className="flex-1 space-y-3 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {/* Edit Permissions Banner */}
                {isEditMode && editPermissions && !editPermissions.canEdit && (
                  <div className="rounded-md p-2.5 bg-red-50 border border-red-200">
                    <div className="flex items-start gap-2">
                      <Info className="h-4 w-4 mt-0.5 flex-shrink-0 text-red-600" />
                      <div>
                        <p className="font-medium text-xs text-red-800">
                          View Only
                        </p>
                        <p className="text-xs text-red-600 mt-0.5">{editPermissions.reason}</p>
                      </div>
                    </div>
                  </div>
                )}
                {isEditMode && editPermissions && editPermissions.canEdit && !canAssignToOthers && (
                  <div className="rounded-md p-2.5 bg-blue-50 border border-blue-200">
                    <div className="flex items-start gap-2">
                      <Info className="h-4 w-4 mt-0.5 flex-shrink-0 text-blue-600" />
                      <div>
                        <p className="font-medium text-xs text-gray-800">
                          Edit Mode
                        </p>
                        <p className="text-xs text-gray-600 mt-0.5">{editPermissions.reason}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Center - superadmin only */}
                {user?.userRole === 'superadmin' && (
                  <div className="space-y-1.5">
                    <Label htmlFor="organization" className="text-xs font-semibold text-gray-700">Organization *</Label>
                    <Select
                      value={selectedOrgId ? selectedOrgId.toString() : ''}
                      onValueChange={(value) => setSelectedOrgId(parseInt(value))}
                      disabled={loadingOrganizations}
                    >
                      <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                        <SelectValue placeholder={loadingOrganizations ? "Loading..." : "Select center"} />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.isArray(organizationsData?.items) && organizationsData.items.map((org) => (
                          <SelectItem key={org.id} value={org.id.toString()}>{org.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Team */}
                {availableTeams.length > 0 && (
                  <div className="space-y-1.5">
                    <Label htmlFor="team" className="text-xs font-semibold text-gray-700">Team *</Label>
                    <Select
                      value={selectedTeamId ? selectedTeamId.toString() : ''}
                      onValueChange={(value) => setSelectedTeamId(parseInt(value))}
                      disabled={loadingTeams || !canEditOrderDetails}
                    >
                      <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${!canEditOrderDetails ? 'bg-gray-50' : ''}`}>
                        <SelectValue placeholder={loadingTeams ? "Loading..." : "Select team"} />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.isArray(availableTeams) && availableTeams.map((team) => (
                          <SelectItem key={team.id} value={team.id.toString()}>{team.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* No teams message */}
                {!loadingTeams && availableTeams.length === 0 && (user?.userRole !== 'superadmin' || selectedOrgId) && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <p className="text-xs text-yellow-800 font-medium">
                      {isAdminOrSuperadmin ? "No teams found in this center" : "You are not assigned to any active teams"}
                    </p>
                  </div>
                )}

                {/* File Number & Division */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="fileNumber" className="text-xs font-semibold text-gray-700">File Number *</Label>
                    <div className="relative">
                      <Input
                        id="fileNumber"
                        placeholder={teamNotSelected ? "Select team first" : "Enter file number"}
                        value={fileNumber}
                        onChange={(e) => {
                          setFileNumber(e.target.value)
                          // Reset check state when typing
                          setFileNumberExists(false)
                          setCanAddStep2(false)
                          setCanAddStep1(false)
                          setExistingOrderId(null)
                          setIsDuplicateEntry(false)
                          setSelectedDuplicateAssigneeId(null)
                        }}
                        onBlur={handleFileNumberBlur}
                        disabled={(isEditMode && !canAssignToOthers) || teamNotSelected}
                        className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${((isEditMode && !canAssignToOthers) || teamNotSelected) ? 'bg-gray-50' : ''}`}
                      />
                      {isCheckingFileNumber && (
                        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
                      )}
                    </div>

                    {isEditMode && canEditEntryDate && (
                      <div className="mt-3 space-y-1.5">
                        <Label htmlFor="entryDate" className="text-xs font-semibold text-gray-700">Entry Date *</Label>
                        <Input
                          id="entryDate"
                          type="date"
                          value={entryDate}
                          onChange={(e) => setEntryDate(e.target.value)}
                          disabled={!canEditEntryDate}
                          className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${!canEditEntryDate ? 'bg-gray-50' : ''}`}
                        />
                      </div>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="division" className="text-xs font-semibold text-gray-700">Division *</Label>
                    <Select
                      value={selectedDivisionId ? selectedDivisionId.toString() : ''}
                      onValueChange={(value) => setSelectedDivisionId(parseInt(value))}
                      disabled={!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                    >
                      <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                        <SelectValue placeholder={teamNotSelected ? "Select team first" : "Select division"} />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.isArray(divisions) && divisions.filter(d => d.isActive !== false).map((division) => (
                          <SelectItem key={division.id} value={division.id.toString()}>{division.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Property Type */}
                <div className="space-y-1.5">
                  <Label htmlFor="propertyType" className="text-xs font-semibold text-gray-700">Property Type *</Label>
                  <Select
                    value={selectedPropertyTypeId ? selectedPropertyTypeId.toString() : ''}
                    onValueChange={(value) => setSelectedPropertyTypeId(value ? parseInt(value) : null)}
                    disabled={!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                  >
                    <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                      <SelectValue placeholder={teamNotSelected ? "Select team first" : "Select property type"} />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(propertyTypes) && propertyTypes.filter(p => p.isActive !== false).map((pt) => (
                        <SelectItem key={pt.id} value={pt.id.toString()}>{pt.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* State & County */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="state" className="text-xs font-semibold text-gray-700">State *</Label>
                    <Select
                      value={selectedState || undefined}
                      onValueChange={setSelectedState}
                      disabled={loadingTeamDetails || !canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                    >
                      <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                        <SelectValue placeholder={teamNotSelected ? "Select team first" : (loadingTeamDetails ? "Loading..." : "Select state")} />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.isArray(availableStates) && availableStates.map((state) => (
                          <SelectItem key={state} value={state}>{state}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="county" className="text-xs font-semibold text-gray-700">County *</Label>
                    <Input
                      id="county"
                      placeholder={teamNotSelected ? "Select team first" : "Enter county"}
                      value={county}
                      onChange={(e) => setCounty(e.target.value)}
                      disabled={!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                      className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}
                    />
                  </div>
                </div>

                {/* Product Type */}
                <div className="space-y-1.5">
                  <Label htmlFor="productType" className="text-xs font-semibold text-gray-700">Product Type *</Label>
                  <Select
                    value={selectedProductType || undefined}
                    onValueChange={handleProductTypeChange}
                    disabled={loadingTeamDetails || !canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                  >
                    <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                      <SelectValue placeholder={teamNotSelected ? "Select team first" : (loadingTeamDetails ? "Loading..." : "Select product type")} />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(availableProducts) && availableProducts.map((product) => (
                        <SelectItem key={product} value={product}>{product}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Production Type */}
                <div className="space-y-1.5">
                  <Label htmlFor="productionType" className="text-xs font-semibold text-gray-700">Production Type *</Label>
                  <Select
                    value={selectedProductionType}
                    onValueChange={(value: 'regular' | 'OT') => setSelectedProductionType(value)}
                    disabled={!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                  >
                    <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                      <SelectValue placeholder="Select production type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="regular">Regular</SelectItem>
                      <SelectItem value="OT">OT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Transaction Type */}
                <div className="space-y-1.5">
                  <Label htmlFor="transactionType" className="text-xs font-semibold text-gray-700">Transaction Type *</Label>
                  <Select
                    value={selectedTransactionTypeId ? selectedTransactionTypeId.toString() : ''}
                    onValueChange={(value) => setSelectedTransactionTypeId(parseInt(value))}
                    disabled={!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1}
                  >
                    <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                      <SelectValue placeholder={teamNotSelected ? "Select team first" : "Select transaction type"} />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(transactionTypes) && transactionTypes.filter(t => t.isActive !== false).map((type) => (
                        <SelectItem key={type.id} value={type.id.toString()}>{type.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Work Assignment */}
            <div className="border border-gray-200 rounded-md p-4 bg-white flex flex-col shadow-sm overflow-hidden">
              <h3 className="text-sm font-semibold border-b border-gray-200 pb-2 mb-4 text-gray-800">
                Work Assignment
              </h3>

              <div className="flex-1 space-y-3 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {!teamNotSelected && (
                  <>
                    {/* Process Type */}
                    <div className="space-y-1.5">
                      <Label htmlFor="processType" className="text-xs font-semibold text-gray-700">Process Type *</Label>
                      <Select
                        value={selectedProcessTypeId ? selectedProcessTypeId.toString() : ''}
                        onValueChange={(value) => setSelectedProcessTypeId(parseInt(value))}
                        disabled={!canEditOrderDetails || teamNotSelected || availableProcessTypes.length === 0 || canAddStep2 || canAddStep1}
                      >
                        <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!canEditOrderDetails || teamNotSelected || availableProcessTypes.length === 0 || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                          <SelectValue placeholder={teamNotSelected ? "Select team first" : (availableProcessTypes.length === 0 ? "No process available" : "Select process type")} />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.isArray(availableProcessTypes) && availableProcessTypes.map((type) => (
                            <SelectItem key={type.id} value={type.id.toString()}>{type.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Order Status */}
                    <div className="space-y-1.5">
                      <Label htmlFor="orderStatus" className="text-xs font-semibold text-gray-700">Order Status *</Label>
                      <Select
                        value={selectedOrderStatusId ? selectedOrderStatusId.toString() : ''}
                        onValueChange={(value) => setSelectedOrderStatusId(parseInt(value))}
                        disabled={!(canEditOrderDetails || canEditOrderStatus) || teamNotSelected || canAddStep2 || canAddStep1}
                      >
                        <SelectTrigger className={`h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${(!(canEditOrderDetails || canEditOrderStatus) || teamNotSelected || canAddStep2 || canAddStep1) ? 'bg-gray-50' : ''}`}>
                          <SelectValue placeholder={teamNotSelected ? "Select team first" : "Select status"} />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.isArray(orderStatuses) && orderStatuses.filter(s => s.isActive !== false).map((status) => (
                            <SelectItem key={status.id} value={status.id.toString()}>{status.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Duplicate order assignee */}
                    {!isEditMode && canAssignToOthers && isDuplicateEntry && (
                      <div className="space-y-1.5">
                        <Label htmlFor="duplicateAssignee" className="text-xs font-semibold text-gray-700">Assign To *</Label>
                        <Select
                          value={selectedDuplicateAssigneeId ? selectedDuplicateAssigneeId.toString() : ''}
                          onValueChange={(value) => setSelectedDuplicateAssigneeId(parseInt(value))}
                          disabled={loadingTeamMembers || teamMemberOptions.length === 0}
                        >
                          <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                            <SelectValue placeholder={loadingTeamMembers ? 'Loading users...' : 'Select team member'} />
                          </SelectTrigger>
                          <SelectContent>
                            {teamMemberOptions.map((assignee) => (
                              <SelectItem key={assignee.id} value={assignee.id.toString()}>{assignee.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {teamMemberOptions.length === 0 && !loadingTeamMembers && (
                          <p className="text-[11px] text-red-600">
                            No active team members available for duplicate assignment in this team.
                          </p>
                        )}
                      </div>
                    )}
                  </>
                )}

                {/* Step Assignment */}
                {!teamNotSelected && (
                  <div className="space-y-3">
                    {/* Step 1 */}
                    {showStep1Section && (
                      <div className="border border-gray-200 rounded-md p-3.5 bg-gray-50">
                        <div className="text-xs font-semibold text-gray-800 mb-3">
                          {selectedProcessType?.name === 'Single Seat' ? 'Single Seat' : 'Step 1'}
                        </div>

                        {/* Assign To dropdown - admin/team lead only */}
                        {canAssignToOthers && !isDuplicateEntry && (
                          <div className="mb-3">
                            <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Assign To *</Label>
                            <Select
                              value={step1UserId ? step1UserId.toString() : ''}
                              onValueChange={(value) => {
                                const userId = parseInt(value)
                                setStep1UserId(userId)
                                // For Single Seat, sync step2 user
                                if (selectedProcessType?.name === 'Single Seat') {
                                  setStep2UserId(userId)
                                }
                              }}
                              disabled={loadingTeamMembers}
                            >
                              <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 bg-white">
                                <SelectValue placeholder={loadingTeamMembers ? "Loading..." : "Select team member"} />
                              </SelectTrigger>
                              <SelectContent>
                                {teamMemberOptions.map((member) => (
                                  <SelectItem key={member.id} value={member.id.toString()}>{member.label}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            {teamMemberOptions.length === 0 && !loadingTeamMembers && (
                              <p className="text-[11px] text-red-600 mt-1">No team members available.</p>
                            )}
                          </div>
                        )}

                        {/* FA Name Selection - everyone needs this */}
                        {(canAssignToOthers || canEditStep1) && (
                          <div className="mb-3">
                            <Label className="text-xs font-medium text-gray-700 mb-1.5 block">FA Name *</Label>
                            <Select
                              value={step1FaNameId ? step1FaNameId.toString() : undefined}
                              onValueChange={(value) => setStep1FaNameId(parseInt(value))}
                            >
                              <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 bg-white">
                                <SelectValue placeholder={loadingFaNames ? "Loading..." : "Select FA name"} />
                              </SelectTrigger>
                              <SelectContent>
                                {Array.isArray(faNames) && faNames.map((fn) => {
                                  const displayName = fn.faName || fn.name || String(fn.id)
                                  return (
                                    <SelectItem key={fn.id} value={fn.id.toString()}>
                                      {displayName}
                                    </SelectItem>
                                  )
                                })}
                              </SelectContent>
                            </Select>
                          </div>
                        )}

                        {/* Read-only Step 1 info for examiners */}
                        {!canAssignToOthers && isEditMode && order?.step1 && !canEditStep1 && (
                          <div className="text-xs text-gray-600 mb-3">
                            <span className="font-medium">{order.step1.userName || order.step1.userName}</span>
                          </div>
                        )}

                        {/* Date Inputs - Removed (no longer needed) */}
                      </div>
                    )}

                    {/* Step 2 */}
                    {showStep2Section && selectedProcessType?.name !== 'Single Seat' && (
                      <div className="border border-gray-200 rounded-md p-3.5 bg-gray-50">
                        <div className="text-xs font-semibold text-gray-800 mb-3">Step 2</div>

                        {/* Assign To dropdown - admin/team lead only */}
                        {canAssignToOthers && !isDuplicateEntry && (
                          <div className="mb-3">
                            <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Assign To *</Label>
                            <Select
                              value={step2UserId ? step2UserId.toString() : ''}
                              onValueChange={(value) => setStep2UserId(parseInt(value))}
                              disabled={loadingTeamMembers}
                            >
                              <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 bg-white">
                                <SelectValue placeholder={loadingTeamMembers ? "Loading..." : "Select team member"} />
                              </SelectTrigger>
                              <SelectContent>
                                {teamMemberOptions.map((member) => (
                                  <SelectItem key={member.id} value={member.id.toString()}>{member.label}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            {teamMemberOptions.length === 0 && !loadingTeamMembers && (
                              <p className="text-[11px] text-red-600 mt-1">No team members available.</p>
                            )}
                          </div>
                        )}

                        {/* FA Name Selection - everyone needs this */}
                        {(canAssignToOthers || canEditStep2) && (
                          <div className="mb-3">
                            <Label className="text-xs font-medium text-gray-700 mb-1.5 block">FA Name *</Label>
                            <Select
                              value={step2FaNameId ? step2FaNameId.toString() : undefined}
                              onValueChange={(value) => setStep2FaNameId(parseInt(value))}
                            >
                              <SelectTrigger className="h-9 text-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500 bg-white">
                                <SelectValue placeholder={loadingFaNames ? "Loading..." : "Select FA name"} />
                              </SelectTrigger>
                              <SelectContent>
                                {Array.isArray(faNames) && faNames.map((fn) => {
                                  const displayName = fn.faName || fn.name || String(fn.id)
                                  return (
                                    <SelectItem key={fn.id} value={fn.id.toString()}>
                                      {displayName}
                                    </SelectItem>
                                  )
                                })}
                              </SelectContent>
                            </Select>
                          </div>
                        )}

                        {/* Read-only Step 2 info for examiners */}
                        {!canAssignToOthers && isEditMode && order?.step2 && !canEditStep2 && (
                          <div className="text-xs text-gray-600 mb-3">
                            <span className="font-medium">{order.step2.userName || order.step2.userName}</span>
                          </div>
                        )}

                        {/* Date Inputs - Removed (no longer needed) */}
                      </div>
                    )}
                  </div>
                )}

                {/* Placeholder when team not selected */}
                {teamNotSelected && (
                  <div className="flex items-center justify-center h-full min-h-[200px] text-gray-400">
                    <div className="text-center">
                      <Info className="h-10 w-10 mx-auto mb-2 opacity-40" />
                      <p className="text-sm font-medium text-gray-500">Select a team to begin</p>
                      <p className="text-xs text-gray-400 mt-1">Choose a team from the left to configure order details</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="mt-4 flex-shrink-0">
            {isEditMode && editPermissions && !editPermissions.canEdit ? (
              <div className="w-full h-11 flex items-center justify-center text-sm font-semibold text-red-600 bg-red-50 border border-red-200 rounded-md">
                Editing is locked — {editPermissions.reason}
              </div>
            ) : (
            <Button 
              type="submit" 
              disabled={submitting || !isFormValid} 
              className="w-full h-11 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isEditMode ? 'Updating Order...' : 'Saving Order...'}
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  {isEditMode ? 'Update Order' : 'Save Order'}
                </>
              )}
            </Button>
            )}
          </div>
        </form>
      )}

      <Dialog
        open={duplicateChoiceOpen}
        onOpenChange={(open) => {
          if (!open) clearDuplicateChoice()
          else setDuplicateChoiceOpen(true)
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>File already exists</DialogTitle>
            <DialogDescription>
              Choose whether to update the existing entry or create a duplicate entry for this file.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (pendingDuplicateCheck) applyExistingOrderChoice(pendingDuplicateCheck)
              }}
            >
              Edit existing entry
            </Button>
            <Button
              type="button"
              onClick={applyDuplicateEntryChoice}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Duplicate entry
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default OrderForm
