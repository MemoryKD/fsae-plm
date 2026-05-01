import { defineStore } from 'pinia'
import api from '../api'

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
        },
        logout() {
            this.token = ''
            this.user = null
            localStorage.removeItem('token')
            localStorage.removeItem('user')
        },
    },
})
