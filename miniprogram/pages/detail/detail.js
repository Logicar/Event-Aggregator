const TYPE_LABELS = {
  conference: '会议', forum: '论坛', lecture: '讲座', seminar: '研讨会', workshop: '工作坊'
}
const MATERIAL_LABELS = {
  video: '回放视频', slides: 'PPT/讲义', document: '文档', minutes: '会议纪要', summary: '总结/回顾'
}

Page({
  data: { event: null },
  onLoad(options) {
    const id = options.id
    const app = getApp()
    const all = [...(app.globalData.events || []), ...(app.globalData.archive || [])]
    let ev = all.find(e => e.id === id)
    if (ev) {
      ev = {
        ...ev,
        typeLabel: TYPE_LABELS[ev.type] || ev.type,
        materialsLabel: (ev.materials || []).map(m => ({ ...m, label: MATERIAL_LABELS[m.type] || m.type }))
      }
      this.setData({ event: ev })
    } else {
      wx.showToast({ title: '未找到该活动', icon: 'none' })
    }
  },
  openUrl(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      // 网页需在小程序后台配置业务域名
      wx.setClipboardData({ data: url, success: () => wx.showToast({ title: '链接已复制', icon: 'none' }) })
    }
  }
})
