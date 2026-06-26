/**
 * Utility helpers for common functions used across the application
 */

import type { UserRole } from '../types'

export const PACIFIC_TIME_ZONE = 'America/Los_Angeles'

/**
 * Extracts initials from a name string
 * @param name - The full name or username
 * @returns Two-letter initials in uppercase
 */
export const getInitials = (name: string): string => {
  if (!name) return ''
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Handles logout flow by logging out user and redirecting to login page
 * @param logout - Zustand logout function from auth store
 * @param navigate - React Router navigate function
 */
export const handleLogoutFlow = async (
  logout: () => Promise<void> | void,
  navigate: (path: string) => void
): Promise<void> => {
  await logout()
  navigate('/login')
}

/**
 * Extracts user-friendly error message from various error response formats
 * Handles string errors, validation error arrays, and error objects
 * @param error - The error object from API response
 * @param defaultMsg - Default message if no error details found
 * @returns Formatted error message string
 */
export const parseApiError = (error: any, defaultMsg: string = 'An error occurred'): string => {
  const detail = error.response?.data?.detail
  if (!detail) return defaultMsg

  if (typeof detail === 'string') {
    return detail
  } else if (Array.isArray(detail)) {
    // Handle Pydantic validation errors (422)
    return detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
  } else if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail)
  }
  return defaultMsg
}

/**
 * Compares user roles in a case-insensitive manner
 * @param userRole - The user's role from backend (may be uppercase)
 * @param expectedRole - The role to compare against (lowercase)
 * @returns True if roles match (case-insensitive)
 */
export const isUserRole = (userRole: string | undefined, expectedRole: UserRole): boolean => {
  return userRole?.toLowerCase() === expectedRole.toLowerCase()
}

/**
 * Checks if user has any of the specified roles (case-insensitive)
 * @param userRole - The user's role from backend (may be uppercase)
 * @param allowedRoles - Array of allowed roles (lowercase)
 * @returns True if user has any of the allowed roles
 */
export const hasAnyUserRole = (userRole: string | undefined, allowedRoles: UserRole[]): boolean => {
  if (!userRole) return false
  return allowedRoles.some(role => role.toLowerCase() === userRole.toLowerCase())
}

/**
 * Gets display name for a user role
 * @param role - The user role
 * @returns Formatted display name
 */
export const getRoleDisplayName = (role: string): string => {
  const lowerRole = role?.toLowerCase()
  switch (lowerRole) {
    case 'superadmin':
      return 'Super Admin'
    case 'admin':
      return 'Admin'
    case 'team_lead':
      return 'Team Lead'
    case 'examiner':
      return 'Examiner'
    default:
      return 'Unknown'
  }
}

/**
 * Gets CSS classes for role badge styling
 * @param role - The user role
 * @returns CSS class string for badge styling
 */
export const getRoleBadgeColor = (role: string): string => {
  const lowerRole = role?.toLowerCase()
  switch (lowerRole) {
    case 'superadmin':
      return 'bg-red-100 text-red-700 border-red-200'
    case 'admin':
      return 'bg-purple-100 text-purple-700 border-purple-200'
    case 'team_lead':
      return 'bg-blue-100 text-blue-700 border-blue-200'
    case 'examiner':
      return 'bg-green-100 text-green-700 border-green-200'
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200'
  }
}

const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})/
const DATE_TIME_PATTERN = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?)?$/

const buildUtcDate = (
  year: number,
  month: number,
  day: number,
  hour = 0,
  minute = 0,
  second = 0,
  millisecond = 0
) => new Date(Date.UTC(year, month - 1, day, hour, minute, second, millisecond))

export const createStableDate = (
  year: number,
  monthIndexZeroBased: number,
  day: number,
  hour = 12
): Date => buildUtcDate(year, monthIndexZeroBased + 1, day, hour)

const parseStoredDateParts = (dateString: string): [number, number, number] | null => {
  const match = dateString.match(DATE_ONLY_PATTERN)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])

  if (!year || !month || !day) return null
  return [year, month, day]
}

const parseStoredDateTimeParts = (
  dateString: string
): [number, number, number, number, number, number, number] | null => {
  const match = dateString.match(DATE_TIME_PATTERN)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const hour = Number(match[4] ?? 0)
  const minute = Number(match[5] ?? 0)
  const second = Number(match[6] ?? 0)
  const millisecond = Number((match[7] ?? '0').padEnd(3, '0'))

  if (!year || !month || !day) return null
  return [year, month, day, hour, minute, second, millisecond]
}

export const formatStoredDate = (
  dateString: string | null | undefined,
  locale: string = 'en-US',
  options?: Intl.DateTimeFormatOptions
): string => {
  if (!dateString) return '-'

  const parsedParts = parseStoredDateParts(dateString)
  if (parsedParts) {
    const [year, month, day] = parsedParts
    const stableDate = buildUtcDate(year, month, day, 12)
    return new Intl.DateTimeFormat(locale, {
      ...options,
      timeZone: 'UTC',
    }).format(stableDate)
  }

  const fallbackDate = new Date(dateString)
  if (Number.isNaN(fallbackDate.getTime())) return '-'

  return new Intl.DateTimeFormat(locale, {
    ...options,
    timeZone: 'UTC',
  }).format(fallbackDate)
}

export const formatStoredDateTime = (
  dateString: string | null | undefined,
  locale: string = 'en-US',
  options?: Intl.DateTimeFormatOptions
): string => {
  if (!dateString) return '-'

  const parsedDateTime = parseStoredDateTimeParts(dateString)
  if (parsedDateTime) {
    const [year, month, day, hour, minute, second, millisecond] = parsedDateTime
    const stableDate = buildUtcDate(year, month, day, hour, minute, second, millisecond)
    return new Intl.DateTimeFormat(locale, {
      ...options,
      timeZone: 'UTC',
    }).format(stableDate)
  }

  const fallbackDate = new Date(dateString)
  if (Number.isNaN(fallbackDate.getTime())) return '-'

  return new Intl.DateTimeFormat(locale, {
    ...options,
    timeZone: 'UTC',
  }).format(fallbackDate)
}

export const parseStoredDateToUtcDate = (dateString: string): Date | null => {
  const parsedParts = parseStoredDateParts(dateString)
  if (!parsedParts) return null

  const [year, month, day] = parsedParts
  return buildUtcDate(year, month, day, 12)
}

export const getPacificDateString = (date: Date = new Date()): string => {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: PACIFIC_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date)

  const year = parts.find((part) => part.type === 'year')?.value
  const month = parts.find((part) => part.type === 'month')?.value
  const day = parts.find((part) => part.type === 'day')?.value

  if (!year || !month || !day) return ''
  return `${year}-${month}-${day}`
}

export const getPacificTodayDate = (date: Date = new Date()): Date => {
  const dateString = getPacificDateString(date)
  const parsed = parseStoredDateToUtcDate(dateString)
  return parsed ?? buildUtcDate(date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate(), 12)
}

export const getPacificMonthKey = (date: Date = new Date()): string => {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: PACIFIC_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
  }).formatToParts(date)

  const year = parts.find((part) => part.type === 'year')?.value
  const month = parts.find((part) => part.type === 'month')?.value
  if (!year || !month) return ''
  return `${year}-${month}`
}

export const formatPacificMonthLabel = (year: number, monthIndexZeroBased: number): string => {
  const stableDate = buildUtcDate(year, monthIndexZeroBased + 1, 1, 12)
  return new Intl.DateTimeFormat('default', {
    month: 'long',
    timeZone: 'UTC',
  }).format(stableDate)
}

export const getPacificWeekStartDate = (weekOffset = 0): string => {
  const today = getPacificTodayDate()
  const dayOfWeek = today.getUTCDay()
  const currentWeekSunday = new Date(today)
  currentWeekSunday.setUTCDate(today.getUTCDate() - dayOfWeek + weekOffset * 7)
  return currentWeekSunday.toISOString().slice(0, 10)
}

export const getPstDateInputValue = (date: Date = new Date()): string => {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Los_Angeles',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date)

  const year = parts.find((part) => part.type === 'year')?.value
  const month = parts.find((part) => part.type === 'month')?.value
  const day = parts.find((part) => part.type === 'day')?.value

  if (!year || !month || !day) {
    const localYear = date.getFullYear()
    const localMonth = String(date.getMonth() + 1).padStart(2, '0')
    const localDay = String(date.getDate()).padStart(2, '0')
    return `${localYear}-${localMonth}-${localDay}`
  }

  return `${year}-${month}-${day}`
}
