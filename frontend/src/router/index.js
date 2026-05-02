/**
 * Vue Router 路由配置
 * 使用 HTML5 History 模式，所有业务页面嵌套在 Layout 布局组件内
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
    // 登录页独立于主布局，不显示侧边栏
    { path: '/login', component: () => import('../views/Login.vue') },
    {
        // 主布局：包含侧边栏和顶部导航，子路由渲染在 <router-view> 中
        path: '/',
        component: () => import('../components/Layout.vue'),
        children: [
            { path: '', redirect: '/parts' },  // 根路径默认跳转零件列表
            { path: 'parts', component: () => import('../views/PartList.vue') },
            { path: 'parts/:id', component: () => import('../views/PartDetail.vue') },
            { path: 'bom/:id', component: () => import('../views/BomView.vue') },
            { path: 'users', component: () => import('../views/UserManage.vue') },
            { path: 'templates', component: () => import('../views/TemplateManage.vue') },
            { path: 'knowledge', component: () => import('../views/KnowledgeBase.vue') },
            { path: 'roles', component: () => import('../views/RoleManage.vue') },
            { path: 'approvals', component: () => import('../views/ApprovalList.vue') },
            { path: 'pending-users', component: () => import('../views/PendingUsers.vue') },
        ],
    },
]

const router = createRouter({ history: createWebHistory(), routes })

// 全局前置守卫：未登录用户只能访问 /login，其他页面重定向到登录页
router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.path !== '/login' && !auth.token) return '/login'
})

export default router
