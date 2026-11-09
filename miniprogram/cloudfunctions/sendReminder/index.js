// 订阅消息云函数骨架（需开通云开发并配置定时触发器）
// 功能：每日定时拉取 events.json，对「即将截止/即将开始」的活动，
//       向已订阅用户发送订阅消息（含时间/地点/报名截止）。
// 前置：在云数据库建 `subscriptions` 集合（字段：openid, eventId, templateId 等）。
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const FEED_URL = 'https://Logicar.github.io/Event-Aggregator/data/events.json'

exports.main = async () => {
  // TODO: 1) 拉取 Feed
  // const events = await fetchFeed(FEED_URL)

  // TODO: 2) 读取订阅记录（openid + 活动 id）
  // const db = cloud.database()
  // const subs = await db.collection('subscriptions').get()

  // TODO: 3) 过滤即将截止/开始的活动（如 deadline 或 start_date 在 0~3 天内）

  // TODO: 4) 逐条调用 subscribeMessage.send 推送模板消息
  // await cloud.openapi.subscribeMessage.send({
  //   touser: openid,
  //   templateId: 'TEMPLATE_ID',
  //   page: 'pages/detail/detail?id=' + eventId,
  //   data: {
  //     thing1: { value: title },       // 活动名称
  //     date2: { value: start_date },   // 举办时间
  //     thing3: { value: venue },       // 举办地点
  //     date4: { value: registration_deadline } // 报名截止
  //   }
  // })

  return { ok: true, note: '骨架实现：接入时按注释补全 Feed 拉取、订阅查询与消息发送' }
}

// 云函数内拉取外部 JSON（需在云函数配置中允许外网访问，或使用 got/axios）
async function fetchFeed(url) {
  const https = require('https')
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = ''
      res.on('data', (c) => (data += c))
      res.on('end', () => resolve(JSON.parse(data)))
    }).on('error', reject)
  })
}
