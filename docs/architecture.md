# 架构文档

## 1. 定位

面向生命科学 / 医学药学 / AI4Science 三大领域，聚合会议、论坛、讲座信息，并对外提供：

- 飞书妙搭定时推送（优先）
- GitHub Pages 网页前端
- 微信小程序（延后）

## 2. 数据流

```
数据源（静态网站 + 公众号/小红书/抖音）
   │
   │  Python 抓取管道
   ▼
采集 → 清洗(normalize) → 去重(dedup) → 状态判定(status) → 归档拆分(archive) → 导出(export)
   │
   ▼
data/events.json（upcoming/ongoing）  +  data/archive.json（ended + materials）
   │
   ▼  GitHub Actions 每日 cron + 手动触发，随 Pages 发布
公开 JSON Feed ──► 飞书妙搭 / 微信小程序 / Web 前端
```

## 3. 核心模块

| 模块 | 路径 | 职责 |
|---|---|---|
| 采集 | `scrapers/` | 静态站点引擎 + 流媒体平台适配器 |
| 清洗 | `pipeline/normalize.py` | 中文日期/区间、地域、领域、报名条件归一化 |
| 去重 | `pipeline/dedup.py` | URL+标题指纹，跨平台合并 |
| 状态 | `pipeline/status.py` | 以“当天(Asia/Shanghai)”判定 upcoming/ongoing/ended |
| 归档 | `pipeline/archive.py` | ended 记录拆分 + materials 采集 |
| 导出 | `pipeline/export.py` | 生成 events.json / archive.json |

## 4. 状态判定

- `start_date >= 当天` → `upcoming`
- `start_date <= 当天 <= end_date` → `ongoing`
- `end_date < 当天` → `ended`（转入归档，仅保留资料链接）

统一使用 `Asia/Shanghai` 时区。时间缺失的活动进入人工复核，不直接推送。

## 5. 数据模型

见 `data/schema.json`。活动与归档共用同一结构，仅 `status` 与 `materials` 区分。

## 6. 部署

- `pipeline.yml`：每日定时（cron，UTC 换算到北京时间上午）+ 手动 `workflow_dispatch`；抓取后提交 `data/events.json`、`data/archive.json`。
- `deploy-pages.yml`：`data/`、`web/` 变更时构建 Vite 站点并发布 GitHub Pages，JSON Feed 随站点公开。

## 7. 飞书妙搭

见 `feishu/README.md`：多维表格 + 自动化（定时触发 → HTTP 拉取 Feed → 新增或更新 → 推送新活动卡片）。

## 8. 合规与稳健性

- 尊重 robots.txt、限速、退避、合理 UA。
- 流媒体平台仅聚合公开内容与原文链接，不转存受版权保护内容；遵守平台条款。
- 单源失败不影响整体，Action 失败告警。
