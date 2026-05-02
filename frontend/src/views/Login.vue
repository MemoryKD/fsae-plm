<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>FSAE-PLM {{ isRegister ? '注册' : '登录' }}</h2>
      <el-form @submit.prevent="handleSubmit">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item v-if="isRegister">
          <el-select v-model="role" placeholder="角色" style="width:100%">
            <el-option label="设计师" value="designer" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isRegister">
          <el-input v-model="team" placeholder="团队（可选）" />
        </el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading" style="width:100%">
          {{ isRegister ? '注册' : '登录' }}
        </el-button>
        <div class="toggle-text">
          <span v-if="isRegister">已有账号？<el-link type="primary" @click="isRegister = false">去登录</el-link></span>
          <span v-else>没有账号？<el-link type="primary" @click="isRegister = true">去注册</el-link></span>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const role = ref('designer')
const team = ref('')
const loading = ref(false)
const isRegister = ref(false)

async function handleSubmit() {
    loading.value = true
    try {
        if (isRegister.value) {
            await api.post('/auth/register', {
                username: username.value,
                password: password.value,
                role: role.value,
                team: team.value || undefined
            })
            await auth.login(username.value, password.value)
            router.push('/')
        } else {
            await auth.login(username.value, password.value)
            router.push('/')
        }
    } catch (e) {} finally {
        loading.value = false
    }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; height: 100vh; background: #f5f7fa; }
.login-card { width: 400px; }
.toggle-text { text-align: center; margin-top: 12px; color: #909399; font-size: 14px; }
</style>
