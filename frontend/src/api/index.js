/**
 * Axios HTTP 客户端实例
 * 统一处理请求/响应拦截：自动注入 JWT token、全局错误处理
 * 所有 API 调用均通过此实例发送
 */
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

// 基础路径，开发环境通过 vite proxy 转发到后端
const api = axios.create({ baseURL: '/api' })

// 请求拦截器：自动为每个请求附加 JWT token 到 Authorization 头
api.interceptors.request.use(config => {
    const auth = useAuthStore()
    if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
    return config
})

// 响应拦截器：统一处理 401 未授权和其他错误
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401 && error.config.url !== '/auth/login') {
            // token 过期或无效：自动登出并跳转登录页
            useAuthStore().logout()
            window.location.href = '/login'
        } else if (error.response?.status !== 401) {
            // 非 401 错误：弹出后端返回的错误信息或默认提示
            ElMessage.error(error.response?.data?.detail || '请求失败')
        }
        return Promise.reject(error)
    }
)

export default api
