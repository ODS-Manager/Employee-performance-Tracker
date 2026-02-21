import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { useDashboardFilterStore, getMonthOptions, getYearOptions } from '../../store/dashboardFilterStore'
import { organizationsApi } from '../../services/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select'
import { Filter } from 'lucide-react'

interface GlobalFiltersProps {
  showOrgFilter?: boolean  // Control whether to show org filter
  className?: string
}

export const GlobalFilters = ({ showOrgFilter = true, className = '' }: GlobalFiltersProps) => {
  const { user } = useAuthStore()
  const {
    filterMonth,
    filterYear,
    filterOrgId,
    setFilterMonth,
    setFilterYear,
    setFilterOrgId,
  } = useDashboardFilterStore()
  
  const isSuperadmin = user?.userRole === 'superadmin'
  
  // Fetch organizations for superadmin filter
  const { data: orgsData } = useQuery({
    queryKey: ['organizations', 'list', 'active'],
    queryFn: () => organizationsApi.list({ isActive: true }),
    enabled: isSuperadmin && showOrgFilter,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Filter className="h-4 w-4 text-slate-500" />
      
      {/* Center Filter - Only for Superadmin */}
      {isSuperadmin && showOrgFilter && orgsData?.items && (
        <Select 
          value={filterOrgId || 'all'} 
          onValueChange={(value) => setFilterOrgId(value === 'all' ? null : value)}
        >
          <SelectTrigger className="w-[140px] h-8 text-xs">
            <SelectValue placeholder="Center" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Centers</SelectItem>
            {orgsData.items.map((org) => (
              <SelectItem key={org.id} value={String(org.id)}>
                {org.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      
      <Select 
        value={filterMonth} 
        onValueChange={setFilterMonth}
      >
        <SelectTrigger className="w-[110px] h-8 text-xs">
          <SelectValue placeholder="Month" />
        </SelectTrigger>
        <SelectContent>
          {getMonthOptions(filterYear).map((month) => (
            <SelectItem key={month.value} value={month.value}>
              {month.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      <Select 
        value={filterYear} 
        onValueChange={setFilterYear}
      >
        <SelectTrigger className="w-[85px] h-8 text-xs">
          <SelectValue placeholder="Year" />
        </SelectTrigger>
        <SelectContent>
          {getYearOptions().map((year) => (
            <SelectItem key={year.value} value={year.value}>
              {year.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
