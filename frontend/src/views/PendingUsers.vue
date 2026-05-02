<template>
  <div>
    <h3>待审批用户</h3>
    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="full_name" label="姓名" width="120" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="join_year" label="加入年份" width="100" />
      <el-table-column prop="phone" label="联系电话" width="140" />
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="handleApprove(row.id)">批准</el-button>
          <el-button type="danger" size="small" @click="handleReject(row.id)">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && users.length === 0" description="暂无待审批用户" />
  </div>
</template>

<script setup>
/**
 * 待审批用户管理页面（仅管理员可见）
 * 新用户注册后处于待审批状态，管理员可在此批准或拒绝
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const users = ref([])       // 待审批用户列表
const loading = ref(false)

/** 获取所有待审批用户 */
async function fetchUsers() {
    loading.value = true
    try {
        const { data } = await api.get('/auth/pending-users')
        users.value = data
    } catch {} finally {
        loading.value = false
    }
}

/** 批准用户：用户获得登录权限，默认角色为 designer */
async function handleApprove(userId) {
    try {
        await api.post(`/auth/approve/${userId}`)
        ElMessage.success('已批准')
        fetchUsers()
    } catch {}
}

/** 拒绝用户（需二次确认） */
async function handleReject(userId) {
    try {
        await ElMessageBox.confirm('确认拒绝该用户？', '确认')
        await api.post(`/auth/reject/${userId}`)
        ElMessage.success('已拒绝')
        fetchUsers()
    } catch {}
}

/** 格式化时间为中文本地格式 */
function formatTime(t) {
    return t ? new Date(t).toLocaleString('zh-CN') : ''
}

onMounted(fetchUsers)
</script>
