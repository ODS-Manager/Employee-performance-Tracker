/**
 * Tests for helper utility functions
 */

import { isUserRole, hasAnyUserRole, getRoleDisplayName, getRoleBadgeColor } from './helpers'
import type { UserRole } from '../types'

// Test data representing users with different role cases from backend
const testUsers = [
  { userRole: 'SUPERADMIN' },
  { userRole: 'ADMIN' },
  { userRole: 'TEAM_LEAD' },
  { userRole: 'EMPLOYEE' },
  { userRole: 'superadmin' },
  { userRole: 'admin' },
  { userRole: 'team_lead' },
  { userRole: 'examiner' },
]

describe('Role Helper Functions', () => {
  describe('isUserRole', () => {
    it('should handle case-insensitive role comparison', () => {
      expect(isUserRole('SUPERADMIN', 'superadmin')).toBe(true)
      expect(isUserRole('superadmin', 'superadmin')).toBe(true)
      expect(isUserRole('ADMIN', 'admin')).toBe(true)
      expect(isUserRole('admin', 'admin')).toBe(true)
      expect(isUserRole('TEAM_LEAD', 'team_lead')).toBe(true)
      expect(isUserRole('team_lead', 'team_lead')).toBe(true)
      expect(isUserRole('EMPLOYEE', 'examiner')).toBe(true)
      expect(isUserRole('examiner', 'examiner')).toBe(true)
    })

    it('should return false for non-matching roles', () => {
      expect(isUserRole('SUPERADMIN', 'admin')).toBe(false)
      expect(isUserRole('admin', 'superadmin')).toBe(false)
      expect(isUserRole('examiner', 'admin')).toBe(false)
    })

    it('should handle undefined userRole', () => {
      expect(isUserRole(undefined, 'admin')).toBe(false)
    })
  })

  describe('hasAnyUserRole', () => {
    it('should handle case-insensitive role checking against multiple roles', () => {
      expect(hasAnyUserRole('SUPERADMIN', ['admin', 'superadmin'])).toBe(true)
      expect(hasAnyUserRole('ADMIN', ['admin', 'superadmin'])).toBe(true)
      expect(hasAnyUserRole('admin', ['admin', 'superadmin'])).toBe(true)
      expect(hasAnyUserRole('TEAM_LEAD', ['admin', 'superadmin', 'team_lead'])).toBe(true)
      expect(hasAnyUserRole('team_lead', ['admin', 'superadmin', 'team_lead'])).toBe(true)
    })

    it('should return false when user does not have any allowed roles', () => {
      expect(hasAnyUserRole('EMPLOYEE', ['admin', 'superadmin'])).toBe(false)
      expect(hasAnyUserRole('examiner', ['admin', 'superadmin'])).toBe(false)
    })

    it('should handle undefined userRole', () => {
      expect(hasAnyUserRole(undefined, ['admin', 'superadmin'])).toBe(false)
    })
  })

  describe('getRoleDisplayName', () => {
    it('should return proper display names for different role cases', () => {
      expect(getRoleDisplayName('SUPERADMIN')).toBe('Super Admin')
      expect(getRoleDisplayName('superadmin')).toBe('Super Admin')
      expect(getRoleDisplayName('ADMIN')).toBe('Admin')
      expect(getRoleDisplayName('admin')).toBe('Admin')
      expect(getRoleDisplayName('TEAM_LEAD')).toBe('Team Lead')
      expect(getRoleDisplayName('team_lead')).toBe('Team Lead')
      expect(getRoleDisplayName('EMPLOYEE')).toBe('Employee')
      expect(getRoleDisplayName('examiner')).toBe('Employee')
    })

    it('should handle unknown roles', () => {
      expect(getRoleDisplayName('unknown')).toBe('Unknown')
      expect(getRoleDisplayName('')).toBe('Unknown')
    })
  })

  describe('getRoleBadgeColor', () => {
    it('should return appropriate CSS classes for different role cases', () => {
      expect(getRoleBadgeColor('SUPERADMIN')).toBe('bg-red-100 text-red-700 border-red-200')
      expect(getRoleBadgeColor('superadmin')).toBe('bg-red-100 text-red-700 border-red-200')
      expect(getRoleBadgeColor('ADMIN')).toBe('bg-purple-100 text-purple-700 border-purple-200')
      expect(getRoleBadgeColor('admin')).toBe('bg-purple-100 text-purple-700 border-purple-200')
      expect(getRoleBadgeColor('TEAM_LEAD')).toBe('bg-blue-100 text-blue-700 border-blue-200')
      expect(getRoleBadgeColor('team_lead')).toBe('bg-blue-100 text-blue-700 border-blue-200')
      expect(getRoleBadgeColor('EMPLOYEE')).toBe('bg-green-100 text-green-700 border-green-200')
      expect(getRoleBadgeColor('examiner')).toBe('bg-green-100 text-green-700 border-green-200')
    })

    it('should handle unknown roles with default styling', () => {
      expect(getRoleBadgeColor('unknown')).toBe('bg-gray-100 text-gray-700 border-gray-200')
      expect(getRoleBadgeColor('')).toBe('bg-gray-100 text-gray-700 border-gray-200')
    })
  })
})

// Integration test to demonstrate the fix working
describe('Role Comparison Integration', () => {
  it('should correctly identify users with backend UPPERCASE roles as having frontend lowercase roles', () => {
    // Simulate backend returning UPPERCASE role but frontend expecting lowercase
    const backendUser = { userRole: 'SUPERADMIN' }
    
    // These should all work now with case-insensitive comparison
    expect(isUserRole(backendUser.userRole, 'superadmin')).toBe(true)
    expect(hasAnyUserRole(backendUser.userRole, ['admin', 'superadmin'])).toBe(true)
    
    // This user should be able to access superadmin-only features
    const canAccessSuperAdminFeatures = hasAnyUserRole(backendUser.userRole, ['superadmin'])
    expect(canAccessSuperAdminFeatures).toBe(true)
    
    // This user should be able to access admin or superadmin features
    const canAccessAdminFeatures = hasAnyUserRole(backendUser.userRole, ['admin', 'superadmin'])
    expect(canAccessAdminFeatures).toBe(true)
  })

  it('should work with mixed case scenarios', () => {
    const testCases = [
      { backend: 'SUPERADMIN', frontend: 'superadmin', expected: true },
      { backend: 'ADMIN', frontend: 'admin', expected: true },
      { backend: 'TEAM_LEAD', frontend: 'team_lead', expected: true },
      { backend: 'EMPLOYEE', frontend: 'examiner', expected: true },
      { backend: 'superadmin', frontend: 'superadmin', expected: true },
      { backend: 'Admin', frontend: 'admin', expected: true },
      { backend: 'Team_Lead', frontend: 'team_lead', expected: true },
    ]

    testCases.forEach(({ backend, frontend, expected }) => {
      expect(isUserRole(backend, frontend as UserRole)).toBe(expected)
    })
  })
})