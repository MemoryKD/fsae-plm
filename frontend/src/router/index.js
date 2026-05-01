import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
    { path: '/login', component: () => import('../views/Login.vue') },
    {
        path: '/',
        component: () => import('../components/Layout.vue'),
        children: [
            { path: '', redirect: '/parts' },
            { path: 'parts', component: () => import('../views/PartList.vue') },
            { path: 'parts/:id', component: () => import('../views/PartDetail.vue') },
            { path: 'bom/:id', component: () => import('../views/BomView.vue') },
            { path: 'users', component: () => import('../views/UserManage.vue') },
            { path: 'templates', component: () => import('../views/TemplateManage.vue') },
        ],
    },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.path !== '/login' && !auth.token) return '/login'
})

export default router
