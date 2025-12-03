# Audigest 数据库设计文档

## 1. 核心资源表 (source_media)

**用途**：存储视频或播客的元数据，是系统的“总账本”。

| 字段名 (Field)     | 类型 (Type) | 约束 (Constraints)            | 描述 (Description)                              |
| :----------------- | :---------- | :---------------------------- | :---------------------------------------------- |
| `id`               | Integer     | **PK** (主键), Auto Increment | 唯一 ID                                         |
| `original_url`     | String      | **Unique**, Index             | 原始链接 (YouTube/Podcast)，防止重复录入        |
| `title`            | String      | Not Null                      | 视频/播客标题                                   |
| `platform`         | String      | -                             | 来源平台 (例如: `youtube`, `podcast`, `tiktok`) |
| `author`           | String      | Nullable                      | 频道名或播客作者                                |
| `duration`         | Integer     | Nullable                      | 媒体时长 (秒)                                   |
| `local_audio_path` | String      | Nullable                      | 下载到本地的音频文件路径                        |
| `status`           | String      | Default: 'pending'            | 当前处理状态 (详见下方状态枚举)                 |
| `error_msg`        | String      | Nullable                      | 如果失败，记录具体的报错信息                    |
| `created_at`       | DateTime    | Default: Now                  | 创建/入库时间                                   |
| `updated_at`       | DateTime    | Default: Now                  | 最后更新时间                                    |

> **Status 状态枚举值建议：**
>
> - `pending`: 等待队列中
> - `downloading`: 正在下载音频
> - `transcribing`: 正在进行语音转文字
> - `summarizing`: 正在进行 AI 总结
> - `done`: 全部完成
> - `failed`: 发生错误

---

## 2. 逐字稿切片表 (transcript_segment)

**用途**：存储带有时间戳和说话人标签的每一句话。不存大段文本，而是存切片，为了支持精确跳转和声纹修正。

| 字段名 (Field)  | 类型 (Type) | 约束 (Constraints)            | 描述 (Description)                           |
| :-------------- | :---------- | :---------------------------- | :------------------------------------------- |
| `id`            | Integer     | **PK**, Auto Increment        | 唯一 ID                                      |
| `media_id`      | Integer     | **FK** (关联 source_media.id) | 所属的媒体 ID                                |
| `start_time`    | Float       | Not Null                      | 开始时间 (秒)，如 `12.5`                     |
| `end_time`      | Float       | Not Null                      | 结束时间 (秒)，如 `15.8`                     |
| `text`          | String      | Not Null                      | 这段时间内的文字内容                         |
| `speaker_label` | String      | Not Null                      | 原始声纹标签 (如 `SPEAKER_00`)               |
| `speaker_name`  | String      | Nullable                      | 真实人名 (如 `马斯克`)，由 AI 分析或人工填入 |

---

## 3. 智能分析与总结表 (summary)

**用途**：存储 LLM 生成的各种分析结果。设计为“一对多”，因为同一个视频可以有不同版本的总结。

| 字段名 (Field) | 类型 (Type) | 约束 (Constraints)            | 描述 (Description)                                     |
| :------------- | :---------- | :---------------------------- | :----------------------------------------------------- |
| `id`           | Integer     | **PK**, Auto Increment        | 唯一 ID                                                |
| `media_id`     | Integer     | **FK** (关联 source_media.id) | 所属的媒体 ID                                          |
| `summary_type` | String      | Default: 'standard'           | 总结类型 (如 `detail`, `one_sentence`, `mindmap_json`) |
| `content`      | Text        | Not Null                      | **核心内容** (通常是 Markdown 格式的文本)              |
| `tags`         | JSON/String | Nullable                      | AI 提取的标签列表 (如 `["AI", "创业"]`)                |
| `model_used`   | String      | -                             | 使用的模型版本 (如 `gpt-4o`, `llama3-local`)           |
| `created_at`   | DateTime    | Default: Now                  | 生成时间                                               |

---

## 4. 导出记录表 (export_log)

**用途**：记录哪些内容已经导出到了哪些外部平台，防止重复导出，并支持更新操作。

| 字段名 (Field)    | 类型 (Type) | 约束 (Constraints)            | 描述 (Description)                              |
| :---------------- | :---------- | :---------------------------- | :---------------------------------------------- |
| `id`              | Integer     | **PK**, Auto Increment        | 唯一 ID                                         |
| `media_id`        | Integer     | **FK** (关联 source_media.id) | 所属的媒体 ID                                   |
| `target_platform` | String      | Not Null                      | 目标平台 (如 `notion`, `obsidian`, `feishu`)    |
| `external_id`     | String      | Nullable                      | 外部系统的 ID (如 Notion Page ID)，用于后续更新 |
| `status`          | String      | Default: 'success'            | 导出状态 (`success`, `failed`)                  |
| `exported_at`     | DateTime    | Default: Now                  | 导出时间                                        |

---

### 💡 开发者备注 (Implementation Notes)

1.  **数据库引擎**: 推荐使用 `SQLite` (开发阶段) -> `PostgreSQL` (生产阶段)。
2.  **ORM 框架**: 推荐使用 `SQLModel` (Python)，上面的表格可以直接映射为 Class。
3.  **JSON 字段**: `tags` 字段在 SQLite 中通常存储为 Text 字符串，在 PostgreSQL 中可以使用原生的 JSONB 类型。
