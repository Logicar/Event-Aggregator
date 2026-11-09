# 微信小程序（骨架 · AppID 待注册）

本目录为微信小程序骨架。**正式开发前需先注册微信公众平台小程序账号并取得 AppID**（企业主体便于使用订阅消息）。

## 前置条件

1. 注册微信公众平台小程序账号，获取 **AppID**。
2. 在 `project.config.json` 中填入 `appid`。
3. 开通 **云开发**（用于订阅消息定时推送），在 `app.js` 中填入云环境 ID。
4. 数据 Feed 已公开：`https://Logicar.github.io/Event-Aggregator/data/events.json`（在 `utils/api.js` 配置）。
5. 在小程序后台把 `*.github.io` 加入 **request 合法域名**。

## 功能

- 拉取 `events.json`（进行中/未开始）+ `archive.json`（已结束·资料回放）。
- 活动列表 + 详情（时间/地点/**报名链接/报名条件**）。
- 归档视图展示回放视频/文档资料链接。
- 订阅消息提醒（云函数 `cloudfunctions/sendReminder` 每日定时发送）。

## 目录

```
miniprogram/
├── project.config.json       # 开发者工具项目配置（填 AppID）
├── app.json / app.js / app.wxss
├── utils/api.js              # Feed 拉取封装（配置 Feed URL）
├── pages/
│   ├── index/                # 活动列表（活动/归档切换）
│   └── detail/               # 详情（含报名区块 + 资料）
└── cloudfunctions/
    └── sendReminder/         # 订阅消息云函数骨架
```

## 订阅消息提醒（说明）

微信小程序不能像飞书那样由外部直接推送，需用**订阅消息**（用户主动订阅一次，获得一次推送权限）+ 后端定时调用微信接口：

1. 前端：用户点击「提醒我」→ `wx.requestSubscribeMessage` 订阅模板。
2. 存储：将用户 `openid` 与订阅的活动/提醒偏好写入云数据库。
3. 云函数 `sendReminder`：每日定时触发 → 拉取 `events.json` → 对「即将截止/即将开始」的活动，调用 `subscribeMessage.send` 推送模板消息（含时间/地点/报名截止）。
4. 模板消息字段需在公众平台申请模板（类别：活动提醒）。

> 因 AppID 与云环境尚未配置，云函数为骨架实现，接入时按注释补全。
