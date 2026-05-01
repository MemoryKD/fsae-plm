<template>
  <el-container style="height: 100vh">
    <el-aside width="200px" style="background: #304156">
      <div style="color: #fff; padding: 20px; font-size: 18px; font-weight: bold;">FSAE-PLM</div>
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9">
        <el-menu-item index="/parts"><el-icon><Folder /></el-icon><span>零件管理</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/templates"><el-icon><Setting /></el-icon><span>编号规则</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display:flex; align-items:center; justify-content:flex-end; border-bottom: 1px solid #eee;">
        <span>{{ auth.user?.username }} ({{ auth.user?.role }})</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
    auth.logout()
    router.push('/login')
}
</script>
