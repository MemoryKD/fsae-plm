import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
    const auth = useAuthStore()
    if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
    return config
})

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401 && error.config.url !== '/auth/login') {
            useAuthStore().logout()
            window.location.href = '/login'
        } else if (error.response?.status !== 401) {
            ElMessage.error(error.response?.data?.detail || '请求失败')
        }
        return Promise.reject(error)
    }
)

export default api
