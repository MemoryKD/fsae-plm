<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h2>BOM 管理 - {{ partName }}</h2>
      <div>
        <el-button type="primary" @click="showAddDialog = true">添加零件</el-button>
        <el-button type="success" @click="exportBom">导出 Excel</el-button>
      </div>
    </div>

    <el-table :data="bomItems" stripe v-loading="loading">
      <el-table-column prop="part_number" label="零件号" width="150" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="quantity" label="数量" width="80" />
      <el-table-column prop="level" label="层级" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.check_state === '检出' ? 'warning' : 'success'" size="small">
            {{ row.check_state }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" link @click="removeItem(row)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAddDialog" title="添加零件到 BOM" width="500px">
      <el-form>
        <el-form-item label="搜索零件">
          <el-select v-model="selectedPartId" filterable remote :remote-method="searchParts" placeholder="输入零件号搜索">
            <el-option v-for="p in searchResults" :key="p.id" :label="`${p.part_number} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="quantity" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addItem">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * BOM（物料清单）管理页面
 * 功能：查看装配体的子零件列表、添加/移除子零件、导出 Excel
 * BOM 条目会自动关联零件信息（编号、名称、检入/检出状态）
 */
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const route = useRoute()
const partId = route.params.id || route.query.partId  // 支持路由参数和查询参数两种方式传入
const partName = ref('')        // 当前装配体名称
const bomItems = ref([])        // BOM 条目列表
const loading = ref(false)
const showAddDialog = ref(false)  // 添加零件对话框显隐
const selectedPartId = ref(null)  // 选中要添加的零件 ID
const quantity = ref(1)           // 添加数量
const searchResults = ref([])     // 远程搜索结果

/**
 * 获取 BOM 列表并补充零件详情信息
 * BOM 接口只返回 part_id，需逐个查询零件详情以显示编号和名称
 */
async function fetchBom() {
  loading.value = true
  try {
    const { data } = await api.get(`/parts/${partId}/bom`)
    // 并发查询每个 BOM 条目对应的零件详情
    bomItems.value = await Promise.all(data.map(async (item) => {
      try {
        const { data: part } = await api.get(`/parts/${item.part_id}`)
        return { ...item, part_number: part.part_number, name: part.name, check_state: part.check_state }
      } catch {
        return { ...item, part_number: '?', name: '?', check_state: '?' }
      }
    }))
  } finally {
    loading.value = false
  }
}

/** 远程搜索零件（用于添加零件到 BOM 时的选择器） */
async function searchParts(query) {
  if (!query) return
  const { data } = await api.get('/parts/', { params: { search: query } })
  searchResults.value = data
}

/** 添加零件到 BOM */
async function addItem() {
  if (!selectedPartId.value) return
  await api.post(`/parts/${partId}/bom`, { part_id: selectedPartId.value, quantity: quantity.value })
  ElMessage.success('已添加')
  showAddDialog.value = false
  selectedPartId.value = null
  quantity.value = 1
  await fetchBom()
}

/** 从 BOM 中移除零件（需确认） */
async function removeItem(row) {
  await ElMessageBox.confirm('确定移除此零件？', '确认')
  await api.delete(`/parts/${partId}/bom/${row.id}`)
  ElMessage.success('已移除')
  await fetchBom()
}

/** 导出 BOM 为 Excel 文件（新窗口打开下载链接） */
function exportBom() {
  window.open(`/api/parts/${partId}/bom/export`, '_blank')
}

onMounted(async () => {
  await fetchBom()
  try {
    const { data } = await api.get(`/parts/${partId}`)
    partName.value = data.name
  } catch {}
})
</script>
