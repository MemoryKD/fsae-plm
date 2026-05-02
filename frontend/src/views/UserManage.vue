<template>
  <div>
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
      <h2 style="margin:0">用户管理</h2>
    </div>

    <el-table :data="users" stripe v-loading="loading">
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="team" label="团队" width="150">
        <template #default="{ row }">
          {{ row.team || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="200">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" v-if="isAdmin">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openRoleDialog(row)" :disabled="row.id === currentUserId">
            修改角色
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showRoleDialog" title="修改用户角色" width="400px">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="editingUser?.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newRoleId" style="width:100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.display_name" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="updateRole">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const loading = ref(false)
const showRoleDialog = ref(false)
const editingUser = ref(null)
const newRoleId = ref('')

const roles = ref([])
const isAdmin = computed(() => auth.user?.role === 'admin')
const currentUserId = computed(() => auth.user?.id)

function roleLabel(role) {
  return { admin: '管理员', manager: '经理', designer: '设计师', viewer: '查看者' }[role] || role
}

function roleTagType(role) {
  return { admin: 'danger', manager: 'warning', designer: '', viewer: 'info' }[role] || ''
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await api.get('/users')
    users.value = data
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function openRoleDialog(user) {
  editingUser.value = user
  newRoleId.value = user.role_id || ''
  showRoleDialog.value = true
}

async function fetchRoles() {
  const { data } = await api.get('/roles/')
  roles.value = data
}

async function updateRole() {
  try {
    await api.put(`/users/${editingUser.value.id}/role`, { role_id: newRoleId.value })
    ElMessage.success('角色已更新')
    showRoleDialog.value = false
    await fetchUsers()
  } catch {
    // error handled by interceptor
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>
