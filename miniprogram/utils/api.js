// Feed 拉取封装。将 BASE_URL 替换为你的 GitHub Pages 地址。
const BASE_URL = 'https://Logicar.github.io/Event-Aggregator/data/'

function fetchJSON(path) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          resolve(res.data)
        } else {
          reject(new Error('请求失败: ' + res.statusCode))
        }
      },
      fail: reject
    })
  })
}

// 活动 Feed（upcoming/ongoing）
function fetchEvents() {
  return fetchJSON('events.json')
}

// 归档 Feed（ended + materials）
function fetchArchive() {
  return fetchJSON('archive.json')
}

module.exports = { fetchEvents, fetchArchive }
