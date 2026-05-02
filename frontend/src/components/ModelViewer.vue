<template>
  <div ref="container" style="width:100%;height:400px;background:#f0f0f0;border-radius:8px;position:relative">
    <div v-if="loading" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)">加载 3D 模型...</div>
    <div v-if="error" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#999">{{ error }}</div>
  </div>
</template>

<script setup>
/**
 * Three.js 3D 模型预览组件
 * 支持加载 GLTF/GLB 格式的 3D 模型，提供鼠标拖拽旋转/缩放交互
 * 用于零件详情页的 3D 预览功能
 */
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps({ url: String })  // 模型文件的 API 地址
const container = ref(null)  // Three.js 渲染挂载的 DOM 容器
const loading = ref(true)
const error = ref('')

// Three.js 核心对象（非响应式，不需要触发视图更新）
let scene, camera, renderer, controls, animId

/** 初始化 Three.js 场景：创建相机、渲染器、灯光、网格、轨道控制器 */
function init() {
  if (!container.value) return
  const w = container.value.clientWidth
  const h = container.value.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f0f0)

  // 透视相机：45度视角，近裁面0.01，远裁面1000
  camera = new THREE.PerspectiveCamera(45, w / h, 0.01, 1000)
  camera.position.set(1, 1, 1)

  // WebGL 渲染器：开启抗锯齿，适配高分屏
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.value.appendChild(renderer.domElement)

  // 环境光 + 方向光，确保模型各面可见
  const ambient = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambient)
  const dir = new THREE.DirectionalLight(0xffffff, 0.8)
  dir.position.set(5, 5, 5)
  scene.add(dir)

  // 轨道控制器：支持鼠标左键旋转、滚轮缩放、右键平移
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true  // 启用阻尼，使旋转有惯性效果

  // 地面参考网格
  const grid = new THREE.GridHelper(10, 20, 0xcccccc, 0xeeeeee)
  scene.add(grid)

  // 渲染循环：每帧更新控制器状态并渲染场景
  function animate() {
    animId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

/**
 * 加载 GLTF/GLB 模型文件
 * 加载完成后自动计算模型包围盒，居中并缩放到合适大小
 */
function loadModel(url) {
  if (!url || !scene) return
  loading.value = true
  error.value = ''

  const loader = new GLTFLoader()
  loader.load(
    url,
    (gltf) => {
      const model = gltf.scene
      // 计算模型包围盒，居中并缩放到视野内（最大尺寸映射到2个单位）
      const box = new THREE.Box3().setFromObject(model)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())
      const maxDim = Math.max(size.x, size.y, size.z)
      const scale = 2 / maxDim
      model.scale.setScalar(scale)
      model.position.sub(center.multiplyScalar(scale))
      scene.add(model)
      loading.value = false
    },
    undefined,
    (err) => {
      error.value = '3D 模型加载失败'
      loading.value = false
    }
  )
}

/** 窗口大小变化时更新相机比例和渲染器尺寸 */
function handleResize() {
  if (!container.value || !renderer) return
  const w = container.value.clientWidth
  const h = container.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

onMounted(() => {
  init()
  if (props.url) loadModel(props.url)
  window.addEventListener('resize', handleResize)
})

// 监听 url 变化：支持动态切换模型
watch(() => props.url, (newUrl) => {
  if (newUrl) loadModel(newUrl)
})

// 组件卸载时清理资源，防止内存泄漏
onBeforeUnmount(() => {
  if (animId) cancelAnimationFrame(animId)
  if (renderer) renderer.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
