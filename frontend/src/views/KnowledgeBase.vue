<template>
  <div style="display:flex; gap:20px; height:calc(100vh - 140px);">
    <!-- 左侧：板块分类导航栏，点击切换筛选 -->
    <div style="width:220px; flex-shrink:0; border-right:1px solid #eee; padding-right:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <h3 style="margin:0">板块</h3>
        <el-button text type="primary" @click="showCatDialog = true" v-if="isAdmin">+</el-button>
      </div>
      <div
        @click="selectCategory(null)"
        :class="['cat-item', { active: !selectedCat }]"
      >
        <div style="font-weight:500">全部文章</div>
      </div>
      <div
        v-for="cat in categories"
        :key="cat.id"
        @click="selectCategory(cat)"
        :class="['cat-item', { active: selectedCat?.id === cat.id }]"
      >
        <div style="font-weight:500">{{ cat.name }}</div>
        <div style="font-size:12px; color:#999; margin-top:2px;">{{ cat.description }}</div>
      </div>
    </div>

    <!-- 右侧：文章列表，支持搜索和新建 -->
    <div style="flex:1; overflow:auto;">
      <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
        <el-input v-model="search" placeholder="搜索文章..." style="width:300px" @input="fetchArticles" clearable />
        <el-button type="primary" @click="openCreateArticle">+ 新建文章</el-button>
      </div>

      <el-table :data="articles" stripe v-loading="loading" @row-click="viewArticle" style="cursor:pointer">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="author_name" label="作者" width="100" />
        <el-table-column prop="tags" label="标签" width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in parseTags(row.tags)" :key="tag" size="small" style="margin:2px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建/编辑文章对话框：标题、板块、标签、内容（支持简易 Markdown） -->
    <el-dialog v-model="showArticleDialog" :title="editingArticle ? '编辑文章' : '新建文章'" width="800px" top="5vh">
      <el-form :model="articleForm" label-width="60px">
        <el-form-item label="标题" required>
          <el-input v-model="articleForm.title" />
        </el-form-item>
        <el-form-item label="板块" required>
          <el-select v-model="articleForm.category_id" style="width:100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="articleForm.tags" placeholder="用逗号分隔，如：设计规范,悬架,安全" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="articleForm.content" type="textarea" :rows="15" placeholder="支持 Markdown 格式" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showArticleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveArticle">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文章详情对话框：显示内容、附件列表，支持编辑/删除/上传附件 -->
    <el-dialog v-model="showDetail" width="900px" top="3vh">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3 style="margin:0">{{ detailArticle?.title }}</h3>
          <div>
            <el-button size="small" @click="editArticle(detailArticle)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteArticle(detailArticle)">删除</el-button>
          </div>
        </div>
      </template>
      <div v-if="detailArticle" style="line-height:1.8;">
        <div style="color:#999; font-size:13px; margin-bottom:16px;">
          作者: {{ detailArticle.author_name }} | 更新于: {{ formatDate(detailArticle.updated_at) }}
          <span v-if="detailArticle.tags"> | 标签: {{ detailArticle.tags }}</span>
        </div>
        <div class="article-content" v-html="renderContent(detailArticle.content)"></div>

        <!-- Attachments -->
        <el-divider />
        <h4>附件</h4>
        <div v-for="att in attachments" :key="att.id" style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
          <el-button text type="primary" @click="downloadAttachment(att)">{{ att.filename }}</el-button>
          <span style="color:#999; font-size:12px;">{{ formatSize(att.file_size) }}</span>
          <el-button text type="danger" size="small" @click="deleteAttachment(att)" v-if="isAdmin">删除</el-button>
        </div>
        <el-upload
          :action="`/api/knowledge/articles/${detailArticle.id}/attachments`"
          :headers="uploadHeaders"
          :on-success="onUploadSuccess"
          :show-file-list="false"
          style="margin-top:8px;"
        >
          <el-button size="small">上传附件</el-button>
        </el-upload>
      </div>
    </el-dialog>

    <!-- 板块管理对话框：仅管理员可见，可添加/删除板块 -->
    <el-dialog v-model="showCatDialog" title="板块管理" width="500px">
      <div v-for="cat in categories" :key="cat.id" style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
        <el-input :model-value="cat.name" disabled style="flex:1" />
        <el-button text type="danger" @click="deleteCategory(cat)">删除</el-button>
      </div>
      <el-divider />
      <el-form :model="catForm" inline>
        <el-form-item label="名称">
          <el-input v-model="catForm.name" style="width:150px" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="catForm.description" style="width:200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="createCategory">添加</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 知识库页面
 * 功能：按板块分类管理技术文章，支持文章的创建/编辑/删除、附件上传/下载、
 * 关键词搜索、Markdown 内容渲染
 * 布局：左侧板块分类导航 + 右侧文章列表
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => ['admin', 'manager'].includes(auth.user?.role))
// 附件上传需要手动携带 token（el-upload 组件不走 axios 拦截器）
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))

const categories = ref([])       // 板块分类列表
const articles = ref([])         // 文章列表
const attachments = ref([])      // 当前查看文章的附件列表
const selectedCat = ref(null)    // 当前选中的板块（null=全部文章）
const search = ref('')           // 搜索关键词
const loading = ref(false)

const showArticleDialog = ref(false)   // 新建/编辑文章对话框
const editingArticle = ref(null)       // 编辑中的文章（null=新建模式）
const articleForm = ref({ title: '', content: '', category_id: '', tags: '' })

const showDetail = ref(false)     // 文章详情对话框
const detailArticle = ref(null)   // 当前查看的文章

const showCatDialog = ref(false)  // 板块管理对话框
const catForm = ref({ name: '', description: '' })

/** 解析逗号分隔的标签字符串为数组 */
function parseTags(tags) {
  if (!tags) return []
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}

/** 格式化时间为中文本地格式 */
function formatDate(d) {
  return d ? new Date(d).toLocaleString('zh-CN') : '-'
}

/** 格式化文件大小为人类可读格式 */
function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/**
 * 简易 Markdown 渲染：支持粗体、斜体、行内代码、换行
 * 注意：v-html 存在 XSS 风险，此处先转义 HTML 实体再渲染
 */
function renderContent(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

async function fetchCategories() {
  const { data } = await api.get('/knowledge/categories/')
  categories.value = data
}

/** 获取文章列表，支持按板块筛选和关键词搜索 */
async function fetchArticles() {
  loading.value = true
  try {
    const params = {}
    if (selectedCat.value) params.category_id = selectedCat.value.id
    if (search.value) params.search = search.value
    const { data } = await api.get('/knowledge/articles/', { params })
    articles.value = data
  } catch { /* handled */ } finally {
    loading.value = false
  }
}

/** 切换板块筛选 */
function selectCategory(cat) {
  selectedCat.value = cat
  fetchArticles()
}

/** 打开新建文章对话框，默认选中当前板块 */
function openCreateArticle() {
  editingArticle.value = null
  articleForm.value = {
    title: '',
    content: '',
    category_id: selectedCat.value?.id || (categories.value[0]?.id || ''),
    tags: '',
  }
  showArticleDialog.value = true
}

/** 打开编辑文章对话框，填充现有数据 */
function editArticle(article) {
  editingArticle.value = article
  articleForm.value = {
    title: article.title,
    content: article.content || '',
    category_id: article.category_id,
    tags: article.tags || '',
  }
  showDetail.value = false
  showArticleDialog.value = true
}

/** 保存文章（新建或更新） */
async function saveArticle() {
  if (!articleForm.value.title || !articleForm.value.category_id) {
    ElMessage.warning('请填写标题和板块')
    return
  }
  try {
    if (editingArticle.value) {
      await api.put(`/knowledge/articles/${editingArticle.value.id}`, articleForm.value)
      ElMessage.success('文章已更新')
    } else {
      await api.post('/knowledge/articles/', articleForm.value)
      ElMessage.success('文章已创建')
    }
    showArticleDialog.value = false
    await fetchArticles()
  } catch { /* handled */ }
}

/** 查看文章详情（同时加载附件列表） */
async function viewArticle(row) {
  const { data } = await api.get(`/knowledge/articles/${row.id}`)
  detailArticle.value = data
  const attRes = await api.get(`/knowledge/articles/${row.id}/attachments`)
  attachments.value = attRes.data
  showDetail.value = true
}

/** 删除文章（二次确认） */
async function deleteArticle(article) {
  await ElMessageBox.confirm(`确定删除「${article.title}」？`, '确认删除', { type: 'warning' })
  try {
    await api.delete(`/knowledge/articles/${article.id}`)
    ElMessage.success('已删除')
    showDetail.value = false
    await fetchArticles()
  } catch { /* handled */ }
}

/** 下载附件（新窗口打开） */
function downloadAttachment(att) {
  window.open(`/api/knowledge/attachments/${att.id}/download`, '_blank')
}

/** 附件上传成功后刷新附件列表 */
function onUploadSuccess() {
  if (detailArticle.value) {
    api.get(`/knowledge/articles/${detailArticle.value.id}/attachments`).then(r => {
      attachments.value = r.data
    })
  }
}

/** 删除附件（仅管理员可操作） */
async function deleteAttachment(att) {
  await ElMessageBox.confirm(`确定删除附件「${att.filename}」？`, '确认', { type: 'warning' })
  try {
    await api.delete(`/knowledge/attachments/${att.id}`)
    ElMessage.success('已删除')
    attachments.value = attachments.value.filter(a => a.id !== att.id)
  } catch { /* handled */ }
}

/** 创建新板块 */
async function createCategory() {
  if (!catForm.value.name) return
  try {
    await api.post('/knowledge/categories/', catForm.value)
    ElMessage.success('板块已创建')
    catForm.value = { name: '', description: '' }
    await fetchCategories()
  } catch { /* handled */ }
}

/** 删除板块（会同时删除该板块下的所有文章） */
async function deleteCategory(cat) {
  await ElMessageBox.confirm(`确定删除板块「${cat.name}」？其下文章也会被删除。`, '确认', { type: 'warning' })
  try {
    await api.delete(`/knowledge/categories/${cat.id}`)
    ElMessage.success('已删除')
    await fetchCategories()
    if (selectedCat.value?.id === cat.id) selectedCat.value = null
    await fetchArticles()
  } catch { /* handled */ }
}

onMounted(async () => {
  await fetchCategories()
  await fetchArticles()
})
</script>

<style scoped>
.cat-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}
.cat-item:hover { background: #f0f7ff; }
.cat-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }

.article-content { white-space: pre-wrap; word-break: break-word; }
.article-content code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
</style>
