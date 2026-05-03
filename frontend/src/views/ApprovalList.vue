<template>
  <div>
    <h2 style="margin-bottom:20px">待审批列表</h2>
    <el-table :data="notices" stripe v-loading="loading">
      <el-table-column prop="notice_number" label="通告编号" width="150" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="reason" label="变更原因" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === '待审批' ? 'warning' : row.status === '已批准' ? 'success' : 'danger'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <template v-if="row.status === '待审批'">
            <el-button size="small" type="success" @click="handleApprove(row.id, true)">批准</el-button>
            <el-button size="small" type="danger" @click="handleApprove(row.id, false)">拒绝</el-button>
          </template>
          <span v-else style="color:#999;font-size:12px">已处理</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const notices = ref([])
const loading = ref(false)

async function fetchNotices() {
  loading.value = true
  try {
    const { data } = await api.get('/change-notices/pending')
    notices.value = data
  } finally {
    loading.value = false
  }
}

async function handleApprove(id, approved) {
  await api.post(`/change-notices/${id}/approve`, { approved })
  ElMessage.success(approved ? '已批准' : '已拒绝')
  await fetchNotices()
}

onMounted(fetchNotices)
</script>
