<template>
  <div v-if="part">
    <el-page-header @back="$router.back()">
      <template #content>
        <span>{{ part.part_number }} - {{ part.name }}</span>
      </template>
    </el-page-header>

    <el-descriptions :column="2" border style="margin-top:20px">
      <el-descriptions-item label="零件编号">{{ part.part_number }}</el-descriptions-item>
      <el-descriptions-item label="名称">{{ part.name }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ part.type }}</el-descriptions-item>
      <el-descriptions-item label="子系统">{{ part.subsystem }}</el-descriptions-item>
      <el-descriptions-item label="当前版本">{{ part.current_version || 'N/A' }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag>{{ part.workflow_state }}</el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <h3 style="margin-top:30px">版本历史</h3>
    <el-upload
      action="#"
      :http-request="handleUpload"
      :before-upload="beforeUpload"
      style="margin-bottom:15px"
    >
      <el-button type="primary">上传新版本</el-button>
    </el-upload>
    <el-table :data="versions" stripe>
      <el-table-column prop="version_number" label="版本号" width="100" />
      <el-table-column prop="file_type" label="文件类型" width="100" />
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="{ row }">{{ row.file_size ? (row.file_size / 1024).toFixed(1) + ' KB' : '' }}</template>
      </el-table-column>
      <el-table-column prop="comment" label="备注" />
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const part = ref(null)
const versions = ref([])

async function fetchPart() {
    const { data } = await api.get(`/parts/${route.params.id}`)
    part.value = data
}

async function fetchVersions() {
    const { data } = await api.get(`/parts/${route.params.id}/versions`)
    versions.value = data
}

function beforeUpload(file) {
    return true
}

async function handleUpload({ file }) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('version_number', String.fromCharCode(65 + versions.value.length))
    formData.append('comment', '')
    await api.post(`/parts/${route.params.id}/versions`, formData)
    ElMessage.success('上传成功')
    await fetchVersions()
    await fetchPart()
}

onMounted(() => {
    fetchPart()
    fetchVersions()
})
</script>
