# 多维表格字段结构

妙搭多维表格（Base）字段定义，与 `data/schema.json` 对齐。推送表只同步 `events.json`（upcoming/ongoing）。

| 字段名 | 多维表格类型 | 对应 Schema 字段 | 说明 |
|---|---|---|---|
| `id` | 文本（唯一） | `id` | 稳定唯一键，去重/增量依据 |
| `title` | 文本 | `title` | 活动标题 |
| `type` | 单选 | `type` | conference/forum/lecture/seminar/workshop |
| `domains` | 多选 | `domains` | 生命科学/医学药学/AI4Science |
| `fields` | 多选 | `fields` | 细分研究领域 |
| `organizer` | 文本 | `organizer` | 主办方 |
| `institution` | 文本 | `institution` | 主办单位 |
| `province` | 文本 | `province` | 省份 |
| `city` | 文本 | `city` | 城市 |
| `venue` | 文本 | `venue` | 举办地点 |
| `start_date` | 日期 | `start_date` | 开始日期 |
| `end_date` | 日期 | `end_date` | 结束日期 |
| `registration_url` | 链接 | `registration_url` | 报名入口 |
| `registration_deadline` | 日期 | `registration_deadline` | 报名截止 |
| `registration_requirements` | 文本 | `registration_requirements` | 报名条件（换行多条） |
| `url` | 链接 | `url` | 详情页 |
| `source_name` | 文本 | `source_name` | 来源名 |
| `source_type` | 单选 | `source_type` | website/wechat_mp/xiaohongshu/douyin/rss/manual |
| `status` | 单选 | `status` | upcoming/ongoing |
| `summary` | 文本 | `summary` | 简介摘要 |
| `last_updated` | 日期时间 | `last_updated` | 最近更新 |

## 归档表（可选）

若需在飞书内查历史资料，另建「归档」表，额外增加：

| 字段名 | 多维表格类型 | 对应 Schema 字段 | 说明 |
|---|---|---|---|
| `materials` | 文本 | `materials` | 资料链接（每行一个「标题 - URL」） |

归档表从 `archive.json` 同步，字段含 `materials`。
