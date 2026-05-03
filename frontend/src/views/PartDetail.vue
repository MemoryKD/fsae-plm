<template>
  <div v-if="part">
    <el-page-header @back="$router.back()">
      <template #content>
        <span>{{ part.part_number }} - {{ part.name }}</span>
      </template>
    </el-page-header>

    <!-- 零件基本信息卡片：编号、名称、类型、子系统、版本、生命周期状态、检入/检出状态 -->
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

    <template v-if="part.derived_from_id">
      <el-descriptions :column="1" border style="margin-top:10px">
        <el-descriptions-item label="来源">
          <router-link :to="`/parts/${part.derived_from_id}`">查看源零件</router-link>
          <el-tag v-if="part.branch_name" style="margin-left:8px">{{ part.branch_name }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </template>

    <template v-if="lineage.length > 1">
      <h4 style="margin-top:15px">衍生链</h4>
      <el-steps :active="lineage.length - 1" simple style="margin-bottom:15px">
        <el-step v-for="node in lineage" :key="node.id" :title="node.part_number"
          :description="node.branch_name || '原生'" />
      </el-steps>
    </template>

    <template v-if="branches.length > 0">
      <h4 style="margin-top:15px">分支</h4>
      <el-table :data="branches" stripe size="small">
        <el-table-column prop="part_number" label="零件号">
          <template #default="{ row }">
            <router-link :to="`/parts/${row.id}`">{{ row.part_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="branch_name" label="分支名" />
      </el-table>
    </template>

    <div v-if="hasPreview" style="margin-top:20px">
      <h3>3D 预览</h3>
      <ModelViewer :url="`/api/parts/${part.id}/preview`" />
    </div>
    <div v-else style="margin-top:20px">
      <el-button type="primary" @click="generatePreview" :loading="generatingPreview">生成 3D 预览</el-button>
      <span style="color:#999;margin-left:10px;font-size:13px">仅支持 STL/STEP 等通用格式</span>
    </div>

    <!-- 操作按钮区：根据权限和零件状态动态显示可用操作 -->
    <div style="margin-top:20px; display:flex; gap:10px;">
      <!-- 已发布状态：只能取消发布（需创建更改通告走审批流程） -->
      <el-button v-if="auth.hasPermission('unpublish_parts') && part.lifecycle_state === '已发布'" type="warning" @click="showChangeNotice = true">取消发布</el-button>
      <template v-else>
        <!-- 检入状态：可检出（独占编辑）或发布 -->
        <el-button v-if="auth.hasPermission('checkout_parts') && part.check_state === '检入'" type="primary" @click="checkout">检出</el-button>
        <el-button v-if="auth.hasPermission('publish_parts') && part.check_state === '检入'" type="success" @click="publish">发布</el-button>
        <!-- 检出状态：可检入（上传修改后的文件） -->
        <el-button v-if="auth.hasPermission('checkin_parts') && part.check_state === '检出'" type="info" @click="showCheckin = true">检入</el-button>
      </template>
      <el-button @click="showBranch = true">创建分支</el-button>
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

    <el-dialog v-model="showBranch" title="创建分支" width="400px">
      <el-form label-width="80px">
        <el-form-item label="分支名称">
          <el-input v-model="branchName" placeholder="如：轻量化方案" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBranch = false">取消</el-button>
        <el-button type="primary" @click="createBranch">创建</el-button>
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
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="downloadVersion(row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>

    <template v-if="part.type === 'assembly'">
      <h3 style="margin-top:30px">BOM 物料清单</h3>
      <el-button type="primary" size="small" style="margin-bottom:10px" @click="downloadAll">下载全部（装配体+零件）</el-button>
      <el-table :data="bomParts" stripe>
        <el-table-column prop="part_number" label="零件号" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.check_state === '检出' ? 'warning' : 'success'" size="small">{{ row.check_state }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<script setup>
/**
 * 零件详情页面
 * 功能：查看零件信息、版本历史、检入/检出、发布/取消发布（需更改通告审批）、
 * 创建分支、衍生链追溯、BOM 物料清单（装配体）、3D 模型预览
 */
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ModelViewer from '../components/ModelViewer.vue'

const auth = useAuthStore()

const route = useRoute()
const part = ref(null)              // 当前零件基本信息
const versions = ref([])            // 版本历史列表
const showCheckin = ref(false)      // 检入对话框显隐
const showChangeNotice = ref(false) // 更改通告对话框显隐（取消发布时需要）
const cnForm = ref({ title: '', reason: '', description: '' })  // 更改通告表单
const bomParts = ref([])            // BOM 子零件列表（仅装配体）
const hasPreview = ref(false)       // 是否存在 3D 预览文件
const generatingPreview = ref(false) // 是否正在生成预览
const branches = ref([])            // 分支列表
const lineage = ref([])             // 衍生链（从原生零件到当前零件的路径）
const showBranch = ref(false)       // 创建分支对话框显隐
const branchName = ref('')          // 新分支名称

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

/**
 * 上传新版本文件
 * 版本号自动按字母递增：A, B, C, ...
 */
async function handleUpload({ file }) {
    const formData = new FormData()
    formData.append('file', file)
    // 版本号自动生成：取当前版本号的大写字母部分，后端负责递增
    formData.append('version_number', part.value?.current_version || 'A.1')
    formData.append('comment', '')
    await api.post(`/parts/${route.params.id}/versions`, formData)
    ElMessage.success('上传成功')
    await fetchVersions()
    await fetchPart()
}

/**
 * 检出零件：将状态改为"检出"，同时下载当前版本文件
 * 检出后其他用户无法修改此零件
 */
async function checkout() {
    await api.post(`/parts/${route.params.id}/checkout`)
    ElMessage.success('检出成功')
    await fetchPart()
    // 检出后自动触发文件下载（blob 方式）
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

/** 发布零件：将生命周期状态改为"已发布" */
async function publish() {
    await api.post(`/parts/${route.params.id}/publish`)
    ElMessage.success('发布成功')
    await fetchPart()
}

/**
 * 取消发布：需先创建更改通告（需审批）
 * 更改通告包含标题、变更原因、详细说明，提交后等待管理员审批
 */
async function handleUnpublish() {
    if (!cnForm.value.title || !cnForm.value.reason) {
        ElMessage.warning('请填写标题和变更原因')
        return
    }
    // 创建更改通告，审批通过后零件才会真正取消发布
    const { data: cn } = await api.post('/change-notices/', {
        part_id: route.params.id,
        title: cnForm.value.title,
        reason: cnForm.value.reason,
        description: cnForm.value.description,
    })
    ElMessage.success('更改通告已创建，等待审批')
    showChangeNotice.value = false
    cnForm.value = { title: '', reason: '', description: '' }
    await fetchPart()
}

/** 检入零件：上传修改后的文件，将状态改回"检入" */
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

/** 下载指定版本的文件（通过 blob 方式创建临时链接触发下载） */
async function downloadVersion(version) {
    try {
        const response = await api.get(
            `/parts/${route.params.id}/versions/${version.id}/download`,
            { responseType: 'blob' }
        )
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const ext = version.file_type ? `.${version.file_type}` : ''
        link.setAttribute('download', `${part.value.part_number}_${version.version_number}${ext}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    } catch {
        ElMessage.warning('文件下载失败')
    }
}

/** 检查是否存在 3D 预览文件（通过 GET 请求探测） */
async function checkPreview() {
    try {
        await api.get(`/parts/${route.params.id}/preview`, { responseType: 'blob' })
        hasPreview.value = true
    } catch {
        hasPreview.value = false
    }
}

/** 手动触发 3D 预览生成 */
async function generatePreview() {
    generatingPreview.value = true
    try {
        await api.post(`/parts/${route.params.id}/generate-preview`)
        ElMessage.success('3D 预览生成成功')
        hasPreview.value = true
    } catch (e) {
        ElMessage.error(e.response?.data?.detail || '预览生成失败')
    } finally {
        generatingPreview.value = false
    }
}

/** 获取 BOM 子零件列表（仅装配体类型才有） */
async function fetchBomParts() {
    if (part.value?.type === 'assembly') {
        try {
            const { data } = await api.get(`/parts/${route.params.id}/bom/parts`)
            bomParts.value = data
        } catch {}
    }
}

/** 获取该零件的所有分支 */
async function fetchBranches() {
  try {
    const { data } = await api.get(`/parts/${route.params.id}/branches`)
    branches.value = data
  } catch {}
}

/** 获取衍生链：从原生零件到当前零件的完整派生路径 */
async function fetchLineage() {
  try {
    const { data } = await api.get(`/parts/${route.params.id}/lineage`)
    lineage.value = data
  } catch {}
}

/** 创建分支：基于当前零件派生出一个新分支（如"轻量化方案"） */
async function createBranch() {
  if (!branchName.value) {
    ElMessage.warning('请输入分支名称')
    return
  }
  const formData = new FormData()
  formData.append('branch_name', branchName.value)
  await api.post(`/parts/${route.params.id}/branch`, formData)
  ElMessage.success('分支创建成功')
  showBranch.value = false
  branchName.value = ''
  await fetchBranches()
}

/** 下载装配体及其所有子零件（打包下载） */
async function downloadAll() {
    window.open(`/api/parts/${route.params.id}/download-all`, '_blank')
}

onMounted(async () => {
    await fetchPart()
    fetchVersions()
    fetchBomParts()
    checkPreview()
    fetchBranches()
    fetchLineage()
})
</script>
