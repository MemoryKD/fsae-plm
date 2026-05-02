import { defineStore } from 'pinia'
import api from '../api'

function decodeJWT(token) {
    try {
        const payload = token.split('.')[1]
        return JSON.parse(atob(payload))
    } catch { return null }
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: JSON.parse(localStorage.getItem('user') || 'null'),
    }),
    actions: {
        async login(username, password) {
            const { data } = await api.post('/auth/login', { username, password })
            this.token = data.access_token
            localStorage.setItem('token', data.access_token)
            const payload = decodeJWT(data.access_token)
            this.user = {
                id: payload?.sub,
                username: payload?.username || username,
                role: payload?.role || 'designer',
            }
            localStorage.setItem('user', JSON.stringify(this.user))
        },
        logout() {
            this.token = ''
            this.user = null
            localStorage.removeItem('token')
            localStorage.removeItem('user')
        },
    },
})
