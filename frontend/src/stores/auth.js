/**
 * 认证状态管理 Store（Pinia）
 * 负责 JWT token 的存储、登录/登出、权限校验
 * 数据持久化到 localStorage，刷新页面后自动恢复状态
 */
import { defineStore } from 'pinia'
import api from '../api'

/**
 * 解析 JWT token 的 payload 部分
 * JWT 格式: header.payload.signature，payload 为 Base64 编码的 JSON
 */
function decodeJWT(token) {
    try {
        const payload = token.split('.')[1]
        return JSON.parse(atob(payload))
    } catch { return null }
}

export const useAuthStore = defineStore('auth', {
    // 从 localStorage 恢复登录状态，实现页面刷新后免登录
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: JSON.parse(localStorage.getItem('user') || 'null'),
        permissions: JSON.parse(localStorage.getItem('permissions') || '[]'),
    }),
    getters: {
        // 权限判断：检查当前用户是否拥有指定权限
        hasPermission: (state) => (perm) => state.permissions.includes(perm),
    },
    actions: {
        /**
         * 登录：调用后端接口获取 token，解码 JWT 提取用户信息
         * 同时将 token、用户信息、权限列表持久化到 localStorage
         */
        async login(username, password) {
            const { data } = await api.post('/auth/login', { username, password })
            this.token = data.access_token
            localStorage.setItem('token', data.access_token)
            // 从 JWT payload 中提取用户基本信息（sub=用户ID）
            const payload = decodeJWT(data.access_token)
            this.user = {
                id: payload?.sub,
                username: payload?.username || username,
                role: payload?.role || 'designer',
            }
            localStorage.setItem('user', JSON.stringify(this.user))
            this.permissions = data.permissions || []
            localStorage.setItem('permissions', JSON.stringify(this.permissions))
        },
        /** 登出：清空内存状态和 localStorage 中的所有认证数据 */
        logout() {
            this.token = ''
            this.user = null
            this.permissions = []
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            localStorage.removeItem('permissions')
        },
    },
})
