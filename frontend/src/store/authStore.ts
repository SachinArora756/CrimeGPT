import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../api/client'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  station_id: string | null
  badge_number: string | null
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
}

interface RegisterData {
  username: string
  email: string
  password: string
  full_name: string
  role?: string
  station_id?: string
  badge_number?: string
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (username, password) => {
        const response = await api.post('/api/auth/login', { username, password })
        const { access_token, refresh_token, user } = response.data
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        })
      },

      register: async (data) => {
        const response = await api.post('/api/auth/register', data)
        const { access_token, refresh_token, user } = response.data
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        })
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
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
          const { access_token, refresh_token: newRefresh } = response.data
          set({ accessToken: access_token, refreshToken: newRefresh })
        } catch {
          get().logout()
        }
      },
    }),
    { name: 'crimegpt-auth' }
  )
)
