<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h2>角色管理</h2>
      <el-button type="primary" @click="showDialog = true">新建角色</el-button>
    </div>

    <el-table :data="roles" stripe>
      <el-table-column prop="name" label="标识" width="120" />
      <el-table-column prop="display_name" label="显示名称" width="150" />
      <el-table-column label="权限">
        <template #default="{ row }">
          <el-tag v-for="p in row.permissions" :key="p" size="small" style="margin:2px">{{ permLabels[p] || p }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_system === '1' ? 'warning' : 'info'" size="small">
            {{ row.is_system === '1' ? '系统' : '自定义' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="editRole(row)">编辑</el-button>
          <el-button size="small" type="danger" link :disabled="row.is_system === '1'" @click="deleteRole(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editingRole ? '编辑角色' : '新建角色'" width="600px">
      <el-form label-width="80px">
        <el-form-item label="标识">
          <el-input v-model="form.name" :disabled="!!editingRole" placeholder="如 engineer" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" placeholder="如 工程师" />
        </el-form-item>
        <el-form-item label="权限">
          <el-checkbox-group v-model="form.permissions">
            <el-checkbox v-for="(label, key) in permLabels" :key="key" :label="key">{{ label }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const roles = ref([])
const showDialog = ref(false)
const editingRole = ref(null)
const form = ref({ name: '', display_name: '', permissions: [] })

const permLabels = {
  create_parts: '创建零件', edit_parts: '编辑零件', checkout_parts: '检出零件',
  checkin_parts: '检入零件', view_parts: '查看零件', publish_parts: '发布零件',
  unpublish_parts: '取消发布', delete_parts: '删除零件', manage_bom: '管理BOM',
  manage_users: '管理用户', manage_templates: '管理模板', manage_knowledge: '管理知识库',
  manage_workflows: '管理工作流', approve_change_notices: '审批更改通告',
  ban_users: '封禁用户', manage_roles: '管理角色',
}

async function fetchRoles() {
  const { data } = await api.get('/roles/')
  roles.value = data
}

function editRole(row) {
  editingRole.value = row
  form.value = { name: row.name, display_name: row.display_name, permissions: [...row.permissions] }
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  editingRole.value = null
  form.value = { name: '', display_name: '', permissions: [] }
}

async function saveRole() {
  if (!form.value.name || !form.value.display_name) {
    ElMessage.warning('请填写标识和显示名称')
    return
  }
  if (editingRole.value) {
    await api.put(`/roles/${editingRole.value.id}`, {
      display_name: form.value.display_name,
      permissions: form.value.permissions,
    })
    ElMessage.success('角色已更新')
  } else {
    await api.post('/roles/', form.value)
    ElMessage.success('角色已创建')
  }
  closeDialog()
  await fetchRoles()
}

async function deleteRole(row) {
  await ElMessageBox.confirm(`确定删除角色 "${row.display_name}"？`, '确认')
  await api.delete(`/roles/${row.id}`)
  ElMessage.success('角色已删除')
  await fetchRoles()
}

onMounted(fetchRoles)
</script>
