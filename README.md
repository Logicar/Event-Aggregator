# 会议论坛信息聚合平台

面向 **生命科学 / 医学药学 / AI4Science** 三大领域的会议、论坛、讲座信息聚合平台。自动抓取全国高校、机构、企业的活动信息（含静态网站与微信公众号、小红书、抖音等公共流媒体平台），做到：

1. **注明举办地点与时间**
2. **归纳整理报名链接与报名条件**
3. **以“当天”为界区分未开始/进行中与已结束** —— 已结束活动不占日常列表，仅归档其回放视频、文档、PPT 等资料

对外输出：

- **飞书妙搭定时推送**（优先）：每日拉取活动 Feed，向内部员工推送新活动卡片。
- **GitHub Pages 网页前端**：活动检索/筛选 + 报名信息区块 + 归档资料回放视图。
- **微信小程序**（延后）：活动展示 + 订阅消息提醒（需先注册 AppID）。

## 架构一览

```
[数据源：静态网站 + 公众号/小红书/抖音]
        │  Python 抓取管道（配置驱动 + 平台适配器）
        ▼
[GitHub Actions 每日定时任务]  采集 → 清洗 → 去重 → 状态判定(当天) → 归档拆分
        ▼
        ├── data/events.json    活动 Feed（仅 upcoming / ongoing）
        └── data/archive.json   归档 Feed（ended + materials）
        ▼
[GitHub Pages 发布]  →  公开 JSON Feed + Web 前端
        ├── 飞书妙搭 消费 events.json → 定时推送
        └── 微信小程序 消费 events.json / archive.json
```

## 目录结构

```
├── .github/workflows/     # pipeline.yml（定时抓取）+ deploy-pages.yml（发布）
├── sources/sources.yaml   # 数据源注册表（按 source_type 分组）
├── scrapers/              # 抓取引擎：静态站点 + 流媒体平台适配器
├── pipeline/              # normalize / dedup / status / archive / export
├── data/                  # schema.json + events.json + archive.json
├── web/                   # Vite + Vue3 前端
├── feishu/                # 妙搭配置指南 + 表结构 + 卡片模板
├── miniprogram/           # 微信小程序骨架（延后）
└── docs/architecture.md   # 架构文档
```

## 快速开始

### 1. 本地运行抓取管道（Python 3.12）

```bash
pip install -r requirements.txt
python -m pipeline.run --demo          # 用演示数据跑通全流程
python -m pipeline.run --config sources/sources.yaml   # 跑真实数据源
```

输出 `data/events.json` 与 `data/archive.json`。

### 2. 本地运行 Web 前端

```bash
cd web
pnpm install
pnpm dev
```

### 3. 飞书妙搭

参见 [feishu/README.md](feishu/README.md) 的配置指南。

## 数据源接入

在 `sources/sources.yaml` 中按 `source_type` 分组登记数据源。静态站点用 CSS/XPath 选择器配置；公众号/小红书/抖音等平台需登录态，默认走「抓取候选 → 人工确认」半自动流程。

## 状态判定规则

以北京时间（Asia/Shanghai）“当天”为界：

- `start_date >= 当天` → `upcoming`（未开始）
- `start_date <= 当天 <= end_date` → `ongoing`（进行中）
- `end_date < 当天` → `ended`（已结束，转入归档）
