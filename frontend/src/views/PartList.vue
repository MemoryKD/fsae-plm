<template>
  <div>
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
      <el-input v-model="search" placeholder="搜索零件..." style="width:300px" @input="fetchParts" />
      <el-button type="primary" @click="openCreate">+ 新建零件</el-button>
    </div>

    <!-- 零件表格：显示编号、名称、子系统、版本、生命周期、检入/检出状态、分支 -->
    <el-table :data="parts" stripe>
      <el-table-column prop="part_number" label="零件编号" width="150">
        <!-- 零件号可点击跳转到详情页 -->
        <template #default="{ row }">
          <router-link :to="`/parts/${row.id}`" style="color:#409eff">{{ row.part_number }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="subsystem" label="子系统" width="100" />
      <el-table-column prop="current_version" label="版本" width="80" />
      <el-table-column prop="lifecycle_state" label="生命周期" width="100">
        <template #default="{ row }">
          <el-tag :type="row.lifecycle_state === '已发布' ? 'success' : 'info'">{{ row.lifecycle_state }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="check_state" label="检入/检出" width="100">
        <template #default="{ row }">
          <el-tag :type="row.check_state === '检出' ? 'warning' : 'info'">{{ row.check_state }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="branch_name" label="分支" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.branch_name" size="small">{{ row.branch_name }}</el-tag>
          <span v-else style="color:#999">原生</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="deletePart(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建零件对话框：选择模板和子系统后自动生成零件号 -->
    <el-dialog v-model="showCreate" title="新建零件" width="550px" @open="loadTemplates">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="零件名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" @change="updatePreview">
            <el-option label="零件" value="part" />
            <el-option label="装配体" value="assembly" />
            <el-option label="文档" value="document" />
          </el-select>
        </el-form-item>
        <el-form-item label="编号模板" required>
          <el-select v-model="form.template_id" placeholder="选择编号模板" @change="onTemplateChange">
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="子系统" v-if="currentSubsystemCodes.length">
          <el-select v-model="form.subsystem" placeholder="选择子系统" @change="updatePreview">
            <el-option v-for="s in currentSubsystemCodes" :key="s.code" :label="`${s.code} - ${s.desc}`" :value="s.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="零件号预览" v-if="previewNumber">
          <el-tag type="success" size="large" style="font-size:16px; font-family:Consolas;">{{ previewNumber }}</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createPart" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 零件列表页面
 * 功能：搜索零件、新建零件（基于编号模板自动生成零件号）、删除零件
 * 零件号由编号模板规则自动计算生成，用户可实时预览
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const parts = ref([])
const search = ref('')
const showCreate = ref(false)
const creating = ref(false)
const templates = ref([])       // 编号模板列表，新建零件时选择
const previewNumber = ref('')   // 根据模板规则预览生成的零件号
const form = ref({ name: '', type: 'part', template_id: '', subsystem: '' })

// 根据选中的模板提取子系统代码列表（如 SUS=悬架系统, BRK=制动系统）
const currentSubsystemCodes = computed(() => {
  const t = templates.value.find(t => t.id === form.value.template_id)
  if (!t || !t.subsystem_codes) return []
  return Object.entries(t.subsystem_codes).map(([code, desc]) => ({ code, desc }))
})

/** 获取零件列表，支持按关键词搜索 */
async function fetchParts() {
  const { data } = await api.get('/parts', { params: { search: search.value } })
  parts.value = data
}

/** 加载编号模板列表（在新建零件对话框打开时触发） */
async function loadTemplates() {
  try {
    const { data } = await api.get('/templates')
    templates.value = data
  } catch { /* handled */ }
}

/** 切换模板时重置子系统选择；若模板只有一个子系统则自动选中 */
function onTemplateChange() {
  form.value.subsystem = ''
  previewNumber.value = ''
  if (currentSubsystemCodes.value.length === 1) {
    form.value.subsystem = currentSubsystemCodes.value[0].code
    updatePreview()
  }
}

/** 调用后端接口预览下一个可用的零件编号 */
async function updatePreview() {
  if (!form.value.template_id || !form.value.subsystem) {
    previewNumber.value = ''
    return
  }
  try {
    const { data } = await api.get('/parts/next-number', {
      params: { template_id: form.value.template_id, subsystem_code: form.value.subsystem, part_type: form.value.type }
    })
    previewNumber.value = data.part_number
  } catch {
    previewNumber.value = '预览失败'
  }
}

/** 打开新建零件对话框，重置表单 */
function openCreate() {
  form.value = { name: '', type: 'part', template_id: '', subsystem: '' }
  previewNumber.value = ''
  showCreate.value = true
}

/** 创建零件：通过模板规则自动生成零件号 */
async function createPart() {
  if (!form.value.name) {
    ElMessage.warning('请输入零件名称')
    return
  }
  if (!form.value.template_id) {
    ElMessage.warning('请选择编号模板')
    return
  }
  creating.value = true
  try {
    await api.post('/parts/create-with-template', form.value)
    ElMessage.success(`零件 ${previewNumber.value} 创建成功`)
    showCreate.value = false
    form.value = { name: '', type: 'part', template_id: '', subsystem: '' }
    previewNumber.value = ''
    await fetchParts()
  } catch {
    // 错误已由 axios 拦截器统一处理
  } finally {
    creating.value = false
  }
}

/** 删除零件（二次确认后执行） */
async function deletePart(row) {
  await ElMessageBox.confirm(`确定删除「${row.part_number} - ${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await api.delete(`/parts/${row.id}`)
    ElMessage.success('已删除')
    await fetchParts()
  } catch { /* handled */ }
}

onMounted(fetchParts)
</script>
