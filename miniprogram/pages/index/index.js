const api = require('../../utils/api.js')

const TYPE_LABELS = {
  conference: '会议', forum: '论坛', lecture: '讲座', seminar: '研讨会', workshop: '工作坊'
}

Page({
  data: {
    tab: 'active',
    events: [],
    archive: [],
    list: [],
    loading: true
  },
  onLoad() {
    this.load()
  },
  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh())
  },
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ tab }, () => this.applyList())
  },
  applyList() {
    const list = this.data.tab === 'active' ? this.data.events : this.data.archive
    this.setData({ list: list.map(e => ({ ...e, typeLabel: TYPE_LABELS[e.type] || e.type })) })
  },
  load() {
    this.setData({ loading: true })
    return Promise.all([api.fetchEvents(), api.fetchArchive()])
      .then(([a, b]) => {
        const events = a.events || []
        const archive = b.events || []
        getApp().globalData.events = events
        getApp().globalData.archive = archive
        this.setData({ events, archive, loading: false }, () => this.applyList())
      })
      .catch(() => {
        this.setData({ loading: false })
        wx.showToast({ title: '加载失败', icon: 'none' })
      })
  },
  goDetail(e) {
    wx.navigateTo({ url: '/pages/detail/detail?id=' + e.currentTarget.dataset.id })
  }
})
