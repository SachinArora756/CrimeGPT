import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api from '../api/client'

export type UserRole =
  | 'super_admin'
  | 'commissioner'
  | 'acp'
  | 'sho'
  | 'inspector'
  | 'sub_inspector'
  | 'constable'

const ROLE_HIERARCHY: Record<UserRole, number> = {
  super_admin: 7,
  commissioner: 6,
  acp: 5,
  sho: 4,
  inspector: 3,
  sub_inspector: 2,
  constable: 1,
}

const ADMIN_ROLES: UserRole[] = ['super_admin', 'commissioner']
const OFFICER_ROLES: UserRole[] = ['acp', 'sho', 'inspector', 'sub_inspector', 'constable']

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: UserRole
  station_id: string | null
  badge_number: string | null
  department: string | null
  force_password_change?: boolean
}

export type Portal = 'officer' | 'admin'

const INACTIVITY_LIMIT_MS = 20 * 60 * 1000

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  forcePasswordChange: boolean
  portal: Portal | null
  sessionValidated: boolean
  sessionValidating: boolean
  lastActivity: number

  login: (username: string, password: string, portal: Portal) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  validateSession: () => Promise<void>
  hasMinRole: (minRole: UserRole) => boolean
  clearForcePasswordChange: () => void
  isAdmin: () => boolean
  isOfficer: () => boolean
  updateActivity: () => void
  isSessionExpired: () => boolean
}

const AUTH_TIMEOUT_MS = 5000

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      forcePasswordChange: false,
      portal: null,
      sessionValidated: false,
      sessionValidating: false,
      lastActivity: Date.now(),

      updateActivity: () => {
        set({ lastActivity: Date.now() })
      },

      isSessionExpired: () => {
        const { lastActivity, isAuthenticated } = get()
        if (!isAuthenticated) return false
        return Date.now() - lastActivity > INACTIVITY_LIMIT_MS
      },

      login: async (username, password, portal) => {
        const endpoint = portal === 'admin' ? '/api/auth/admin/login' : '/api/auth/login'
        const response = await api.post(endpoint, { username, password })
        const { access_token, refresh_token, user, force_password_change } = response.data
        set({
          user: { ...user, force_password_change: !!force_password_change },
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          forcePasswordChange: !!force_password_change,
          portal,
          sessionValidated: true,
          sessionValidating: false,
          lastActivity: Date.now(),
        })
      },

      logout: () => {
        sessionStorage.removeItem('crimegpt_auth')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          forcePasswordChange: false,
          portal: null,
          sessionValidated: true,
          sessionValidating: false,
          lastActivity: 0,
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          get().logout()
          return
        }
        try {
          const response = await api.post('/api/auth/refresh', { refresh_token: refreshToken })
          const { access_token, refresh_token: newRefresh, user, force_password_change } = response.data
          set({
            accessToken: access_token,
            refreshToken: newRefresh,
            user: user || get().user,
            isAuthenticated: true,
            forcePasswordChange: !!(force_password_change ?? get().forcePasswordChange),
            sessionValidated: true,
            lastActivity: Date.now(),
          })
        } catch {
          get().logout()
        }
      },

      validateSession: async () => {
        const { accessToken, refreshToken } = get()

        if (!accessToken && !refreshToken) {
          set({ sessionValidated: true, sessionValidating: false, isAuthenticated: false })
          return
        }

        if (get().isSessionExpired()) {
          get().logout()
          return
        }

        set({ sessionValidating: true })

        const timeoutController = new AbortController()
        const timeout = setTimeout(() => timeoutController.abort(), AUTH_TIMEOUT_MS)

        try {
          if (accessToken) {
            try {
              const response = await api.get('/api/auth/me', {
                signal: timeoutController.signal,
              })
              const user = response.data
              set({
                user,
                isAuthenticated: true,
                forcePasswordChange: !!user.force_password_change,
                sessionValidated: true,
                sessionValidating: false,
              })
              return
            } catch (e: unknown) {
              const err = e as { name?: string }
              if (err.name === 'CanceledError' || err.name === 'AbortError') {
                throw e
              }
            }
          }

          if (refreshToken) {
            try {
              const response = await api.post('/api/auth/refresh', {
                refresh_token: refreshToken,
              }, { signal: timeoutController.signal })
              const { access_token, refresh_token: newRefresh, user, force_password_change } = response.data
              set({
                accessToken: access_token,
                refreshToken: newRefresh,
                user: user || get().user,
                isAuthenticated: true,
                forcePasswordChange: !!(force_password_change ?? false),
                sessionValidated: true,
                sessionValidating: false,
              })
              return
            } catch (e: unknown) {
              const err = e as { name?: string }
              if (err.name === 'CanceledError' || err.name === 'AbortError') {
                throw e
              }
            }
          }

          get().logout()
        } catch {
          get().logout()
        } finally {
          clearTimeout(timeout)
        }
      },

      hasMinRole: (minRole: UserRole) => {
        const { user } = get()
        if (!user) return false
        return ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[minRole]
      },

      clearForcePasswordChange: () => {
        const { user } = get()
        set({
          forcePasswordChange: false,
          user: user ? { ...user, force_password_change: false } : null,
        })
      },

      isAdmin: () => {
        const { user } = get()
        if (!user) return false
        return ADMIN_ROLES.includes(user.role)
      },

      isOfficer: () => {
        const { user } = get()
        if (!user) return false
        return OFFICER_ROLES.includes(user.role)
      },
    }),
    {
      name: 'crimegpt_auth',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        forcePasswordChange: state.forcePasswordChange,
        portal: state.portal,
        lastActivity: state.lastActivity,
      }),
    }
  )
)
