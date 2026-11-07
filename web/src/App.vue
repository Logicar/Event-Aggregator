<script setup>
import { ref, computed, onMounted } from 'vue'

const BASE = import.meta.env.BASE_URL || './'

const activeEvents = ref([])
const archiveEvents = ref([])
const loading = ref(true)
const error = ref('')

const tab = ref('active') // 'active' | 'archive'
const keyword = ref('')
const domainFilter = ref('')
const typeFilter = ref('')
const provinceFilter = ref('')
const selected = ref(null) // 详情弹层选中的活动

const TYPE_LABELS = {
  conference: '会议',
  forum: '论坛',
  lecture: '讲座',
  seminar: '研讨会',
  workshop: '工作坊'
}
const DOMAIN_COLORS = { 生命科学: 'domain', 医学药学: 'domain', AI4Science: 'domain' }
const MATERIAL_LABELS = {
  video: '回放视频',
  slides: 'PPT/讲义',
  document: '文档',
  minutes: '会议纪要',
  summary: '总结/回顾'
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [a, b] = await Promise.all([
      fetch(`${BASE}data/events.json`).then(r => r.json()),
      fetch(`${BASE}data/archive.json`).then(r => r.json())
    ])
    activeEvents.value = a.events || []
    archiveEvents.value = b.events || []
  } catch (e) {
    error.value = '数据加载失败：' + e.message
  } finally {
    loading.value = false
  }
}

const list = computed(() => (tab.value === 'active' ? activeEvents.value : archiveEvents.value))

const domains = computed(() => [...new Set(activeEvents.value.flatMap(e => e.domains))])
const types = computed(() => [...new Set(activeEvents.value.map(e => e.type))])
const provinces = computed(() =>
  [...new Set(activeEvents.value.map(e => e.province))].filter(Boolean).sort()
)

function nearDeadline(e) {
  if (!e.registration_deadline) return false
  const d = new Date(e.registration_deadline)
  const now = new Date()
  const diff = (d - now) / 86400000
  return diff >= 0 && diff <= 7
}

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return list.value.filter(e => {
    if (domainFilter.value && !e.domains.includes(domainFilter.value)) return false
    if (typeFilter.value && e.type !== typeFilter.value) return false
    if (provinceFilter.value && e.province !== provinceFilter.value) return false
    if (kw) {
      const hay = [e.title, e.organizer, e.institution, e.venue, e.summary,
        ...(e.fields || []), ...(e.keywords || []), ...(e.tags || [])]
        .join(' ').toLowerCase()
      if (!hay.includes(kw)) return false
    }
    return true
  })
})

function fmtDate(s) {
  if (!s) return '待定'
  const [y, m, d] = s.split('-')
  return `${y}年${Number(m)}月${Number(d)}日`
}

function openDetail(e) { selected.value = e }
function closeDetail() { selected.value = null }

onMounted(loadData)
</script>

<template>
  <div>
    <div class="topbar">
      <h1>会议论坛信息聚合</h1>
      <span class="sub">生命科学 · 医学药学 · AI4Science</span>
    </div>
    <div class="domain-pills">
      <span>生命科学</span><span>医学药学</span><span>AI4Science</span>
    </div>

    <div class="tabs">
      <button :class="{ active: tab === 'active' }" @click="tab = 'active'">
        进行中 / 未开始（{{ activeEvents.length }}）
      </button>
      <button :class="{ active: tab === 'archive' }" @click="tab = 'archive'">
        已结束 · 资料回放（{{ archiveEvents.length }}）
      </button>
    </div>

    <div v-if="loading" class="loading">加载中…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else>
      <div class="toolbar">
        <input v-model="keyword" placeholder="搜索标题 / 主办方 / 地点 / 关键词" />
        <select v-model="domainFilter" v-if="tab === 'active'">
          <option value="">全部领域</option>
          <option v-for="d in domains" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="typeFilter" v-if="tab === 'active'">
          <option value="">全部类型</option>
          <option v-for="t in types" :key="t" :value="t">{{ TYPE_LABELS[t] || t }}</option>
        </select>
        <select v-model="provinceFilter" v-if="tab === 'active'">
          <option value="">全部地点</option>
          <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>

      <div v-if="filtered.length === 0" class="empty">暂无匹配的活动</div>

      <div v-for="e in filtered" :key="e.id" class="card" @click="openDetail(e)">
        <p class="card-title">{{ e.title }}</p>
        <div class="badges">
          <span v-for="d in e.domains" :key="d" class="badge domain">{{ d }}</span>
          <span class="badge type">{{ TYPE_LABELS[e.type] || e.type }}</span>
          <span v-if="e.status === 'ongoing'" class="badge status-ongoing">进行中</span>
          <span v-if="nearDeadline(e)" class="badge deadline">报名即将截止</span>
        </div>
        <div class="meta">
          <div class="meta-line"><b>时间</b>：{{ fmtDate(e.start_date) }} — {{ fmtDate(e.end_date) }}</div>
          <div class="meta-line"><b>地点</b>：{{ e.province }} {{ e.city }} · {{ e.venue }}</div>
          <div class="meta-line" v-if="e.organizer"><b>主办</b>：{{ e.organizer }}</div>
          <div class="meta-line" v-if="tab === 'active' && e.registration_deadline">
            <b>报名截止</b>：{{ fmtDate(e.registration_deadline) }}
          </div>
        </div>
        <div class="materials" v-if="tab === 'archive' && e.materials && e.materials.length">
          <a v-for="(m, i) in e.materials" :key="i" class="material-link" :href="m.url" target="_blank" @click.stop>
            {{ MATERIAL_LABELS[m.type] || m.type }}：{{ m.title }}
          </a>
        </div>
      </div>
    </template>

    <!-- 详情弹层 -->
    <div v-if="selected" class="overlay" @click.self="closeDetail()">
      <div class="modal">
        <button class="close" @click="closeDetail()">关闭</button>
        <h2>{{ selected.title }}</h2>
        <div class="badges">
          <span v-for="d in selected.domains" :key="d" class="badge domain">{{ d }}</span>
          <span class="badge type">{{ TYPE_LABELS[selected.type] || selected.type }}</span>
          <span v-if="selected.status === 'ongoing'" class="badge status-ongoing">进行中</span>
        </div>

        <div class="section">
          <h3>时间与地点</h3>
          <div class="meta">
            <div class="meta-line"><b>时间</b>：{{ fmtDate(selected.start_date) }} — {{ fmtDate(selected.end_date) }}</div>
            <div class="meta-line"><b>地点</b>：{{ selected.province }} {{ selected.city }} · {{ selected.venue }}</div>
            <div class="meta-line" v-if="selected.organizer"><b>主办</b>：{{ selected.organizer }}</div>
            <div class="meta-line" v-if="selected.institution"><b>单位</b>：{{ selected.institution }}</div>
          </div>
        </div>

        <div class="section" v-if="selected.status !== 'ended'">
          <h3>报名信息</h3>
          <div class="meta">
            <div class="meta-line" v-if="selected.registration_deadline">
              <b>报名截止</b>：{{ fmtDate(selected.registration_deadline) }}
            </div>
            <div class="meta-line" v-if="selected.abstract_deadline">
              <b>摘要截止</b>：{{ fmtDate(selected.abstract_deadline) }}
            </div>
          </div>
          <ul class="req-list" v-if="selected.registration_requirements && selected.registration_requirements.length">
            <li v-for="(r, i) in selected.registration_requirements" :key="i">{{ r }}</li>
          </ul>
          <div style="margin-top: 10px;">
            <a v-if="selected.registration_url" class="btn primary" :href="selected.registration_url" target="_blank">报名入口</a>
            <a class="btn ghost" :href="selected.url" target="_blank">查看详情</a>
          </div>
        </div>

        <div class="section" v-if="selected.status === 'ended' && selected.materials && selected.materials.length">
          <h3>资料回放</h3>
          <a v-for="(m, i) in selected.materials" :key="i" class="material-link" :href="m.url" target="_blank">
            {{ MATERIAL_LABELS[m.type] || m.type }}：{{ m.title }}
          </a>
        </div>

        <div class="section" v-if="selected.summary">
          <h3>简介</h3>
          <p style="font-size:14px; color:var(--muted);">{{ selected.summary }}</p>
        </div>

        <div class="meta" style="font-size:12px;">
          来源：{{ selected.source_name }}（{{ selected.source_type }}）
        </div>
      </div>
    </div>

    <div class="footer">数据每日自动更新 · 由会议论坛信息聚合平台生成</div>
  </div>
</template>
