import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const NO_RETRY_URLS = ['/api/auth/login', '/api/auth/admin/login', '/api/auth/refresh', '/api/auth/me']

const api = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

let refreshPromise: Promise<void> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const url = originalRequest?.url || ''

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !NO_RETRY_URLS.some((u) => url.includes(u))
    ) {
      originalRequest._retry = true

      if (!refreshPromise) {
        refreshPromise = useAuthStore.getState().refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }

      try {
        await refreshPromise
        const token = useAuthStore.getState().accessToken
        if (!token) throw new Error('No token after refresh')
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      } catch {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
