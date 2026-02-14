import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import { authApi } from '../services/api'

interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setAuth: (user: User) => void
  setUser: (user: User) => void
  logout: () => Promise<void>
  login: (userName: string, password: string) => Promise<void>
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setAuth: (user) => {
        // Tokens are now stored in httpOnly cookies by the server
        // No need to store them in localStorage
        set({ user, isAuthenticated: true })
      },

      setUser: (user) => set({ user }),

      logout: async () => {
        try {
          // Call backend logout to clear httpOnly cookies
          await authApi.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          // Clear local state regardless of backend success
          set({ user: null, isAuthenticated: false })
        }
      },

      login: async (userName: string, password: string) => {
        try {
          set({ isLoading: true })
          const response = await authApi.login({ userName, password })
          
          if (response.success && response.user) {
            get().setAuth(response.user)
          } else {
            throw new Error(response.message || 'Login failed')
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      checkAuth: async () => {
        try {
          // Try to get current user from backend
          // Backend will validate the httpOnly cookie
          const user = await authApi.me()
          set({ user, isAuthenticated: true })
        } catch (error) {
          // If request fails (e.g., cookie expired), clear auth state
          set({ user: null, isAuthenticated: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
