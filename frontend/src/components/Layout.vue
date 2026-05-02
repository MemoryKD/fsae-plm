<template>
  <el-container style="height: 100vh">
    <el-aside width="200px" style="background: #304156">
      <div style="color: #fff; padding: 20px; font-size: 18px; font-weight: bold;">FSAE-PLM</div>
      <!-- router 模式：点击菜单项自动触发路由跳转 -->
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9">
        <el-menu-item index="/parts"><el-icon><Folder /></el-icon><span>零件管理</span></el-menu-item>
        <!-- v-if 权限控制：仅拥有 manage_users 权限的用户可见 -->
        <el-menu-item index="/users" v-if="auth.hasPermission('manage_users')"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/pending-users" v-if="auth.hasPermission('manage_users')"><el-icon><UserFilled /></el-icon><span>待审批用户</span></el-menu-item>
        <el-menu-item index="/templates"><el-icon><Setting /></el-icon><span>编号规则</span></el-menu-item>
        <el-menu-item index="/knowledge"><el-icon><Notebook /></el-icon><span>知识库</span></el-menu-item>
        <el-menu-item index="/approvals" v-if="auth.hasPermission('approve_change_notices')">
          <span>待审批</span>
        </el-menu-item>
        <el-menu-item index="/roles" v-if="auth.hasPermission('manage_roles')">
          <span>角色管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <!-- 顶部栏：显示当前登录用户名和角色，提供退出按钮 -->
      <el-header style="display:flex; align-items:center; justify-content:flex-end; border-bottom: 1px solid #eee;">
        <span>{{ auth.user?.username }} ({{ auth.user?.role }})</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <!-- 主内容区：子路由页面在此渲染 -->
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/**
 * 主布局组件（应用外壳）
 * 包含左侧导航菜单和顶部用户信息栏，根据用户权限动态显示菜单项
 * 所有业务子页面通过 <router-view> 渲染在主内容区
 */
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

/** 退出登录：清除认证状态后跳转到登录页 */
function handleLogout() {
    auth.logout()
    router.push('/login')
}
</script>
