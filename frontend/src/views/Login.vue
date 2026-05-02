<template>
  <div class="login-container">
    <el-card class="login-card">
      <template v-if="registerSuccess">
        <h2>注册成功</h2>
        <el-result icon="success" title="注册申请已提交" sub-title="请等待管理员审批后即可登录" />
        <el-button type="primary" @click="registerSuccess = false; isRegister = false" style="width:100%">返回登录</el-button>
      </template>
      <template v-else>
        <h2>FSAE-PLM {{ isRegister ? '注册' : '登录' }}</h2>
        <el-form @submit.prevent="handleSubmit">
          <el-form-item>
            <el-input v-model="username" placeholder="用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="password" type="password" placeholder="密码" prefix-icon="Lock" />
          </el-form-item>
          <template v-if="isRegister">
            <el-form-item>
              <el-input v-model="fullName" placeholder="姓名 *" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="department" placeholder="部门" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="joinYear" placeholder="加入年份（如 2024）" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="phone" placeholder="联系电话" />
            </el-form-item>
          </template>
          <el-button type="primary" @click="handleSubmit" :loading="loading" style="width:100%">
            {{ isRegister ? '注册' : '登录' }}
          </el-button>
          <div class="toggle-text">
            <span v-if="isRegister">已有账号？<el-link type="primary" @click="isRegister = false">去登录</el-link></span>
            <span v-else>没有账号？<el-link type="primary" @click="isRegister = true">去注册</el-link></span>
          </div>
        </el-form>
      </template>
    </el-card>
  </div>
</template>

<script setup>
/**
 * 登录与注册页面
 * 登录：调用 auth store 的 login action，成功后跳转首页
 * 注册：提交申请后需等待管理员审批，审批通过方可登录
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const fullName = ref('')      // 注册时必填的姓名
const department = ref('')    // 部门（可选）
const joinYear = ref('')      // 加入年份（可选）
const phone = ref('')         // 联系电话（可选）
const loading = ref(false)
const isRegister = ref(false)       // true=注册模式，false=登录模式
const registerSuccess = ref(false)  // 注册成功后显示成功提示

/** 提交表单：注册模式调注册接口，登录模式调登录接口 */
async function handleSubmit() {
    loading.value = true
    try {
        if (isRegister.value) {
            // 注册：后端会将用户设为待审批状态
            await api.post('/auth/register', {
                username: username.value,
                password: password.value,
                full_name: fullName.value,
                department: department.value || undefined,
                join_year: joinYear.value || undefined,
                phone: phone.value || undefined,
            })
            registerSuccess.value = true
        } else {
            // 登录：成功后自动跳转到零件管理首页
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
