<template>
  <div>
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
      <el-input v-model="search" placeholder="搜索零件..." style="width:300px" @input="fetchParts" />
      <el-button type="primary" @click="showCreate = true">+ 新建零件</el-button>
    </div>

    <el-table :data="parts" stripe>
      <el-table-column prop="part_number" label="零件编号" width="150">
        <template #default="{ row }">
          <router-link :to="`/parts/${row.id}`" style="color:#409eff">{{ row.part_number }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="subsystem" label="子系统" width="100" />
      <el-table-column prop="current_version" label="版本" width="80" />
      <el-table-column prop="workflow_state" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="stateType(row.workflow_state)">{{ row.workflow_state }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建零件" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="编号"><el-input v-model="form.part_number" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type">
            <el-option label="零件" value="part" />
            <el-option label="装配体" value="assembly" />
            <el-option label="文档" value="document" />
          </el-select>
        </el-form-item>
        <el-form-item label="子系统"><el-input v-model="form.subsystem" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createPart">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const parts = ref([])
const search = ref('')
const showCreate = ref(false)
const form = ref({ part_number: '', name: '', type: 'part', subsystem: '' })

function stateType(state) {
    return { '设计中': 'info', '审核中': 'warning', '已发布': 'success' }[state] || 'info'
}

async function fetchParts() {
    const { data } = await api.get('/parts', { params: { search: search.value } })
    parts.value = data
}

async function createPart() {
    await api.post('/parts', form.value)
    showCreate.value = false
    form.value = { part_number: '', name: '', type: 'part', subsystem: '' }
    await fetchParts()
}

onMounted(fetchParts)
</script>
