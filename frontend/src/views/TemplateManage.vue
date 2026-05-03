<template>
  <div>
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
      <h2 style="margin:0">编号规则</h2>
      <el-button type="primary" @click="openCreate">+ 新建模板</el-button>
    </div>

    <el-table :data="templates" stripe v-loading="loading">
      <el-table-column prop="name" label="模板名称" width="180" />
      <el-table-column prop="prefix" label="前缀" width="120">
        <template #default="{ row }">{{ row.prefix || '-' }}</template>
      </el-table-column>
      <el-table-column prop="separator" label="分隔符" width="80" />
      <el-table-column prop="digit_count" label="序号位数" width="100" />
      <el-table-column label="子系统代码" min-width="250">
        <template #default="{ row }">
          <el-tag v-for="(desc, code) in row.subsystem_codes" :key="code" style="margin:2px">
            {{ code }}: {{ desc }}
          </el-tag>
          <span v-if="!row.subsystem_codes || Object.keys(row.subsystem_codes).length === 0">-</span>
        </template>
      </el-table-column>
      <el-table-column label="编号示例" width="180">
        <template #default="{ row }">
          <code>{{ previewNumber(row) }}</code>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" v-if="isAdmin">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteTemplate(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editing ? '编辑模板' : '新建编号模板'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="form.name" placeholder="如：底盘零件、动力总成" />
        </el-form-item>
        <el-form-item label="前缀">
          <el-input v-model="form.prefix" placeholder="如：CHS（可留空）" />
        </el-form-item>
        <el-form-item label="分隔符">
          <el-input v-model="form.separator" style="width:80px" />
        </el-form-item>
        <el-form-item label="序号位数">
          <el-input-number v-model="form.digit_count" :min="1" :max="6" />
        </el-form-item>
        <!-- 子系统代码列表：支持拖拽排序（vuedraggable），每项含代码和描述 -->
        <el-form-item label="子系统代码">
          <div style="width:100%">
            <draggable v-model="subsystemList" item-key="code" handle=".drag-handle" style="width:100%">
              <template #item="{ element, index }">
                <div style="display:flex; gap:8px; margin-bottom:8px; align-items:center;">
                  <span class="drag-handle" style="cursor:grab; user-select:none; font-size:18px; color:#909399;">⠿</span>
                  <el-input v-model="element.code" placeholder="代码 如 SUS" style="width:120px" />
                  <el-input v-model="element.desc" placeholder="描述 如 悬架系统" style="flex:1" />
                  <el-button text @click="moveSubsystem(index, -1)" :disabled="index === 0">↑</el-button>
                  <el-button text @click="moveSubsystem(index, 1)" :disabled="index === subsystemList.length - 1">↓</el-button>
                  <el-button type="danger" text @click="subsystemList.splice(index, 1)">删除</el-button>
                </div>
              </template>
            </draggable>
            <el-button text type="primary" @click="subsystemList.push({ code: '', desc: '' })">+ 添加子系统</el-button>
          </div>
        </el-form-item>
        <!-- 类型代码列表：如 PRT=零件、ASM=装配体、DOC=文档 -->
        <el-form-item label="类型代码">
          <div style="width:100%">
            <draggable v-model="typeCodeList" item-key="code" handle=".drag-handle" style="width:100%">
              <template #item="{ element, index }">
                <div style="display:flex; gap:8px; margin-bottom:8px; align-items:center;">
                  <span class="drag-handle" style="cursor:grab; user-select:none; font-size:18px; color:#909399;">⠿</span>
                  <el-input v-model="element.code" placeholder="代码 如 PRT" style="width:120px" />
                  <el-input v-model="element.desc" placeholder="描述 如 零件" style="flex:1" />
                  <el-button text @click="moveTypeCode(index, -1)" :disabled="index === 0">↑</el-button>
                  <el-button text @click="moveTypeCode(index, 1)" :disabled="index === typeCodeList.length - 1">↓</el-button>
                  <el-button type="danger" text @click="typeCodeList.splice(index, 1)">删除</el-button>
                </div>
              </template>
            </draggable>
            <el-button text type="primary" @click="typeCodeList.push({ code: '', desc: '' })">+ 添加类型代码</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 编号规则模板管理页面
 * 功能：创建/编辑/删除编号模板，管理子系统代码和类型代码
 * 零件号格式：前缀 + 类型代码 + 子系统代码 + 序号（如 CHS-PRT-SUS-001）
 * 支持拖拽排序子系统代码和类型代码（使用 vuedraggable）
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import draggable from 'vuedraggable'

const auth = useAuthStore()
const templates = ref([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref(null)           // 编辑中的模板（null 表示新建模式）
const subsystemList = ref([])       // 子系统代码列表（可拖拽排序）
const typeCodeList = ref([])        // 类型代码列表（可拖拽排序）
const form = ref({ name: '', prefix: '', separator: '-', digit_count: 3 })

// 仅管理员和经理角色可编辑/删除模板
const isAdmin = computed(() => ['admin', 'manager'].includes(auth.user?.role))

/**
 * 根据模板规则生成零件号预览示例
 * 格式：前缀-类型代码-子系统代码-序号（用模板定义的分隔符连接）
 */
function previewNumber(row) {
  const parts = []
  if (row.prefix) parts.push(row.prefix)
  const firstType = row.type_codes ? Object.keys(row.type_codes)[0] : ''
  if (firstType) parts.push(firstType)
  const firstCode = row.subsystem_codes ? Object.keys(row.subsystem_codes)[0] : 'XX'
  if (firstCode) parts.push(firstCode)
  parts.push('1'.padStart(row.digit_count || 3, '0'))
  return parts.join(row.separator || '-')
}

async function fetchTemplates() {
  loading.value = true
  try {
    const { data } = await api.get('/templates/')
    templates.value = data
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

/** 打开新建模板对话框，初始化默认类型代码 */
function openCreate() {
  editing.value = null
  form.value = { name: '', prefix: '', separator: '-', digit_count: 3 }
  subsystemList.value = [{ code: '', desc: '' }]
  // 预设三种常用类型代码
  typeCodeList.value = [
    { code: 'PRT', desc: '零件' },
    { code: 'ASM', desc: '装配体' },
    { code: 'DOC', desc: '文档' },
  ]
  showDialog.value = true
}

/** 打开编辑模板对话框，将现有数据填充到表单 */
function openEdit(row) {
  editing.value = row
  form.value = {
    name: row.name,
    prefix: row.prefix || '',
    separator: row.separator || '-',
    digit_count: row.digit_count || 3,
  }
  // 将对象格式转为数组格式以便拖拽编辑
  subsystemList.value = Object.entries(row.subsystem_codes || {}).map(([code, desc]) => ({ code, desc }))
  if (subsystemList.value.length === 0) subsystemList.value.push({ code: '', desc: '' })
  typeCodeList.value = Object.entries(row.type_codes || {}).map(([code, desc]) => ({ code, desc }))
  if (typeCodeList.value.length === 0) typeCodeList.value.push({ code: '', desc: '' })
  showDialog.value = true
}

/** 通过上下箭头移动类型代码的位置 */
function moveTypeCode(index, direction) {
  const target = index + direction
  if (target < 0 || target >= typeCodeList.value.length) return
  const items = [...typeCodeList.value]
  ;[items[index], items[target]] = [items[target], items[index]]
  typeCodeList.value = items
}

/** 通过上下箭头移动子系统代码的位置 */
function moveSubsystem(index, direction) {
  const target = index + direction
  if (target < 0 || target >= subsystemList.value.length) return
  const items = [...subsystemList.value]
  ;[items[index], items[target]] = [items[target], items[index]]
  subsystemList.value = items
}

/**
 * 保存模板：将子系统代码和类型代码列表转为对象格式后提交
 * 仅提交非空的代码项
 */
async function saveTemplate() {
  if (!form.value.name) {
    ElMessage.warning('请输入模板名称')
    return
  }
  // 列表转对象：{ "SUS": "悬架系统", "BRK": "制动系统" }
  const subsystem_codes = {}
  for (const item of subsystemList.value) {
    if (item.code.trim()) subsystem_codes[item.code.trim()] = item.desc.trim()
  }
  const type_codes = {}
  for (const item of typeCodeList.value) {
    if (item.code.trim()) type_codes[item.code.trim()] = item.desc.trim()
  }
  const payload = { ...form.value, subsystem_codes, type_codes }

  try {
    if (editing.value) {
      await api.put(`/templates/${editing.value.id}`, payload)
      ElMessage.success('模板已更新')
    } else {
      await api.post('/templates/', payload)
      ElMessage.success('模板已创建')
    }
    showDialog.value = false
    await fetchTemplates()
  } catch { /* handled */ }
}

/** 删除模板（二次确认） */
async function deleteTemplate(row) {
  await ElMessageBox.confirm(`确定删除模板「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await api.delete(`/templates/${row.id}`)
    ElMessage.success('已删除')
    await fetchTemplates()
  } catch { /* handled */ }
}

onMounted(fetchTemplates)
</script>
