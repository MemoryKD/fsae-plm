<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>FSAE-PLM 登录</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" @click="handleLogin" :loading="loading" style="width:100%">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
    loading.value = true
    try {
        await auth.login(username.value, password.value)
        router.push('/')
    } catch (e) {} finally {
        loading.value = false
    }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; height: 100vh; background: #f5f7fa; }
.login-card { width: 400px; }
</style>
