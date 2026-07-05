import { create } from 'zustand'
import api from '../api/client'

interface Notification {
  id: number
  type: string
  title: string
  message: string
  case_id: number | null
  is_read: boolean
  created_at: string
}

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  fetchNotifications: () => Promise<void>
  fetchUnreadCount: () => Promise<void>
  markRead: (id: number) => Promise<void>
  markAllRead: () => Promise<void>
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,

  fetchNotifications: async () => {
    try {
      set({ loading: true })
      const res = await api.get('/api/notifications/')
      set({ notifications: res.data, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  fetchUnreadCount: async () => {
    try {
      const res = await api.get('/api/notifications/unread-count')
      set({ unreadCount: res.data.count })
    } catch {
      // silent
    }
  },

  markRead: async (id: number) => {
    try {
      await api.put(`/api/notifications/${id}/read`)
      const notifications = get().notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      )
      set({ notifications, unreadCount: Math.max(0, get().unreadCount - 1) })
    } catch {
      // silent
    }
  },

  markAllRead: async () => {
    try {
      await api.put('/api/notifications/mark-all-read')
      const notifications = get().notifications.map((n) => ({ ...n, is_read: true }))
      set({ notifications, unreadCount: 0 })
    } catch {
      // silent
    }
  },
}))
