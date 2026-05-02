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
      <el-descriptions-item label="生命周期">
        <el-tag :type="part.lifecycle_state === '已发布' ? 'success' : 'info'">{{ part.lifecycle_state }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="检入/检出">
        <el-tag :type="part.check_state === '检出' ? 'warning' : 'info'">{{ part.check_state }}</el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <div style="margin-top:20px; display:flex; gap:10px;">
      <el-button v-if="part.lifecycle_state === '已发布'" type="warning" @click="showChangeNotice = true">取消发布</el-button>
      <template v-else>
        <el-button v-if="part.check_state === '检入'" type="primary" @click="checkout">检出</el-button>
        <el-button v-if="part.check_state === '检入'" type="success" @click="publish">发布</el-button>
        <el-button v-if="part.check_state === '检出'" type="info" @click="showCheckin = true">检入</el-button>
      </template>
    </div>

    <el-dialog v-model="showCheckin" title="检入零件" width="400px">
      <el-upload action="#" :http-request="handleCheckin" :before-upload="beforeUpload">
        <el-button type="primary">选择文件并检入</el-button>
      </el-upload>
    </el-dialog>

    <el-dialog v-model="showChangeNotice" title="创建更改通告" width="500px">
      <el-form label-width="80px">
        <el-form-item label="通告标题">
          <el-input v-model="cnForm.title" placeholder="请输入更改通告标题" />
        </el-form-item>
        <el-form-item label="变更原因">
          <el-input v-model="cnForm.reason" type="textarea" placeholder="请输入变更原因" />
        </el-form-item>
        <el-form-item label="详细说明">
          <el-input v-model="cnForm.description" type="textarea" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangeNotice = false">取消</el-button>
        <el-button type="primary" @click="handleUnpublish">确认取消发布</el-button>
      </template>
    </el-dialog>

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
const showCheckin = ref(false)
const showChangeNotice = ref(false)
const cnForm = ref({ title: '', reason: '', description: '' })

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

async function checkout() {
    await api.post(`/parts/${route.params.id}/checkout`)
    ElMessage.success('检出成功')
    await fetchPart()
    // 下载文件
    try {
        const response = await api.get(`/parts/${route.params.id}/download`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${part.value.part_number}_${part.value.current_version}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    } catch (e) {
        ElMessage.warning('文件下载失败')
    }
}

async function publish() {
    await api.post(`/parts/${route.params.id}/publish`)
    ElMessage.success('发布成功')
    await fetchPart()
}

async function handleUnpublish() {
    if (!cnForm.value.title || !cnForm.value.reason) {
        ElMessage.warning('请填写标题和变更原因')
        return
    }
    // 创建更改通告
    const { data: cn } = await api.post('/change-notices/', {
        part_id: route.params.id,
        title: cnForm.value.title,
        reason: cnForm.value.reason,
        description: cnForm.value.description,
    })
    // 自动批准
    await api.post(`/change-notices/${cn.id}/approve`, { approved: true })
    // 取消发布
    await api.post(`/parts/${route.params.id}/unpublish`, null, {
        params: { change_notice_id: cn.id }
    })
    ElMessage.success('取消发布成功')
    showChangeNotice.value = false
    cnForm.value = { title: '', reason: '', description: '' }
    await fetchPart()
}

async function handleCheckin({ file }) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('comment', '')
    await api.post(`/parts/${route.params.id}/checkin`, formData)
    ElMessage.success('检入成功')
    showCheckin.value = false
    await fetchVersions()
    await fetchPart()
}

onMounted(() => {
    fetchPart()
    fetchVersions()
})
</script>
