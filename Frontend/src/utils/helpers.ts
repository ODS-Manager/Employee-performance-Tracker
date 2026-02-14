/**
 * Utility helpers for common functions used across the application
 */

import type { UserRole } from '../types'

/**
 * Extracts initials from a name string
 * @param name - The full name or username
 * @returns Two-letter initials in uppercase
 */
export const getInitials = (name: string): string => {
  if (!name) return '??'
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
export const handleLogoutFlow = (logout: () => void, navigate: (path: string) => void): void => {
  logout()
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
    case 'employee':
      return 'Employee'
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
    case 'employee':
      return 'bg-green-100 text-green-700 border-green-200'
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200'
  }
}
