# HK Travel Planner — 技术报告

> 系统工作流程 · RAG 架构 · AI Agent 设计 · 前后端技术栈

---

## 技术栈概览

| 模块 | 技术 | 说明 |
|------|------|------|
| LLM | OpenAI GPT-4o | via openai Python SDK，function-calling 模式 |
| Web 框架 | Flask | REST API + 静态文件托管 |
| RAG 存储 | SQLite3 | 标准库，零额外依赖，单文件数据库 |
| Excel 解析 | openpyxl | 读取 .xlsx 本地知识库文件 |
| 天气 API | Open-Meteo | 免费、无需 API Key，15 天实况预报 |
| 地图渲染 | Leaflet.js | CDN 引入，轻量开源地图库 |
| 环境配置 | python-dotenv | 本地 .env 加载 OPENAI_API_KEY |
| 生产部署 | Gunicorn + Render | Procfile 配置，支持 PORT 环境变量 |

---

## 1. 系统整体架构

HK Travel Planner 采用 **Flask Web 服务 + AI Agent Pipeline** 的双层架构：

```
用户浏览器
    │  POST /api/plan
    ▼
server.py (Flask)
    │  构建 prompt + 独立获取天气
    ▼
agent.py (GPT-4o Agent Loop)
    ├── food_rag.py  ──→  SQLite (food_places / poi_places / hotel_places)
    ├── data.py      ──→  静态景点 / 酒店 / 交通 / 气候数据
    └── Open-Meteo   ──→  15 天实况天气预报
    │
    ▼  finish_reason == "stop"
结构化 JSON 响应
    │  itinerary + weather_data + attraction_coords
    ▼
static/index.html
    ├── Leaflet.js  ──→  路线地图渲染
    ├── 天气卡片
    └── Day-by-day 行程卡片
```

### 系统层次划分

| 层次 | 组件 | 职责 |
|------|------|------|
| 前端层 | static/index.html + Leaflet.js | 三栏 Map-first Studio，展示行程、天气、路线地图 |
| API 层 | server.py (Flask) | 接收用户参数 → 调用 Agent → 返回 JSON 响应 |
| Agent 层 | agent.py | GPT-4o function-calling 循环，调度 9 个工具 |
| RAG 层 | food_rag.py + SQLite | Excel 知识库 → SQLite → 关键词评分检索 |
| 数据层 | data.py | 静态景点 / 酒店 / 交通 / 天气数据 |
| 外部 API | Open-Meteo | 15 天实时天气预报 |

---

## 2. 系统工作流程

### Step 1 — 用户输入收集（前端）

前端引导用户逐步填写：出发日期与天数、预算档位（low / medium / high）、出行人数与年龄、出行节奏（relaxed / moderate / packed）、兴趣标签（文化 / 美食 / 购物等）、限制条件（避免拥挤 / 减少步行等）、特殊情况（带老人 / 儿童 / 孕妇）及每步的自由文本补充。

```
前端 → POST /api/plan
{
  "start_date": "2026-05-01",
  "days": 3,
  "budget": "medium",
  "pace": "moderate",
  "interests": ["culture", "local_food"],
  "constraints": ["avoid_crowds"],
  "custom_requirements": { "step1_group_dates": "...", ... }
}
```

### Step 2 — 请求构建（server.py）

Flask 后端将结构化参数拼接为自然语言 prompt，同时**独立调用天气 API**（不依赖 LLM 格式），确保前端天气卡片数据稳定可靠。

### Step 3 — RAG 数据库初始化（food_rag.py）

Agent 启动前调用三个 `ensure_*_database()` 函数。系统通过 **MD5 哈希**校验 Excel 文件是否变更，有变更则自动重建 SQLite 表；否则复用缓存，实现增量更新。

### Step 4 — AI Agent 工具调用循环（agent.py）

Agent 进入 `while True` 循环，按推荐顺序依次发起工具调用：

1. `parse_constraints` — 结构化解析旅行者画像
2. `get_weather_forecast` — 获取天气预报
3. `get_attractions` — 过滤静态景点候选
4. `search_poi_rag` — RAG 检索景点
5. `search_food_rag` — RAG 检索餐厅
6. `search_hotel_rag` — RAG 检索酒店
7. `get_hotel_recommendations` — 结构化酒店方案
8. `calculate_budget` — 预算分解
9. `get_transport_info`（按需）— 区间交通信息

`finish_reason == "tool_calls"` 时执行工具并追加结果；`finish_reason == "stop"` 时输出最终行程文本。

### Step 5 — 响应组装与前端渲染

Flask 将行程文本、结构化天气数据、景点坐标字典一并返回。前端解析 `map_data` JSON 块驱动 Leaflet.js 绘制路线，解析天气结构体渲染天气卡片。用户不满意时，`regeneration_feedback` 作为高优先级约束重新触发 Agent。

---

## 3. RAG 系统设计

本项目采用轻量级 **Keyword-Scoring RAG**（基于 Excel → SQLite 的本地检索增强生成），无需向量数据库，适合中小规模结构化本地知识库。

### 知识库来源

| 文件 | 内容 | 字段 |
|------|------|------|
| MIS-香港美食01-60家.xlsx | 60 家餐厅 | 菜系、餐厅名、地点、菜品口味、价位、环境卫生、服务、性价比、菜系口味特色 |
| HK 酒店+景点.xlsx (Sheet1) | 酒店数据 | 名称、位置、星级/地段、亮点、价格区间、适合人群、周边、体验标签 |
| HK 酒店+景点.xlsx (Sheet2) | 景点数据 | 名称、位置、类别、亮点、游览时长、价格、适合人群、体验标签 |

### SQLite 数据库表结构

**`food_places`**
```
cuisine, restaurant, location, dishes_flavor, price,
ambience_hygiene, service, value_note, flavor_by_cuisine,
searchable_text  ← 所有字段拼接的全文检索入口
```

**`poi_places`**
```
attraction, location, category, highlights, duration,
price, suitable_for, experience_tags, searchable_text
```

**`hotel_places`**
```
hotel, location, star_position, highlights, price_range,
suitable_for, nearby, experience_tags, searchable_text
```

**`meta`**：记录每个数据源的文件名与 MD5，用于增量更新判断。

### 索引构建机制

每条记录将所有文本字段拼接为小写 `searchable_text`，作为全文检索的统一入口。系统启动时对 Excel 文件计算 MD5 并与 `meta` 表比对——仅在文件内容变更时触发全量重建。

### 关键词评分检索算法

| 匹配维度 | 得分 | 说明 |
|---------|------|------|
| 查询词命中 searchable_text | +2 / 词 | query 按空格分词，逐词扫描全文 |
| 区域 / 地点精确匹配 | +3 | preferred_area 命中 location 字段 |
| 菜系 / 类别精确匹配 | +3 | preferred_cuisines / preferred_categories 命中对应字段 |
| 预算关键词匹配 | +1 / 词 | budget_level 映射关键词列表（如 low → 'cheap', 'street'） |
| 特定意图词命中 | +2 | 如 'local_food' 命中 'local' 或 'street' |

所有记录按得分降序排序，截取 `top_k` 条（最大 20）返回给 LLM。

### 与 Embedding RAG 对比

| 维度 | 本项目（Keyword Scoring） | Embedding RAG |
|------|--------------------------|--------------|
| 依赖 | SQLite + openpyxl | 向量数据库 + embedding 模型 |
| 部署复杂度 | 极低，单文件数据库 | 需维护向量索引 |
| 语义理解 | 词汇级匹配 | 语义相似度匹配 |
| 适用场景 | 结构化、字段清晰的本地知识库 | 大规模、模糊语义检索 |
| 更新成本 | MD5 检测 + 自动重建 | 需重新 embedding 并更新索引 |

---

## 4. AI Agent 设计

### Function Calling 机制

Agent 使用 OpenAI **Function Calling**（`tools` 参数）将 9 个工具以 JSON Schema 形式暴露给模型。后端拦截 `finish_reason == "tool_calls"`，执行对应 Python 函数，将结果以 `role: "tool"` 消息追加回对话历史，再次调用模型，直到 `finish_reason == "stop"` 输出最终行程。

```python
while True:
    response = client.chat.completions.create(model=MODEL, tools=TOOLS, messages=messages)
    finish = response.choices[0].finish_reason

    if finish == "stop":
        return msg.content        # 最终行程文本

    if finish == "tool_calls":
        for tc in msg.tool_calls:
            result = _run_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
        continue
```

### 工具清单与数据来源

| 工具名 | 数据来源 | 返回内容 |
|--------|---------|---------|
| `parse_constraints` | 用户输入（LLM 解析） | 结构化旅行者画像 |
| `get_weather_forecast` | Open-Meteo API / data.py 月均气候 | 逐日天气（温度 / 湿度 / 降雨概率 / 建议） |
| `get_attractions` | data.py 静态数据 | 按兴趣 / 预算 / 无障碍过滤排序的景点列表 |
| `search_poi_rag` | SQLite poi_places | 关键词评分检索的景点候选 |
| `search_food_rag` | SQLite food_places | 关键词评分检索的餐厅候选 |
| `search_hotel_rag` | SQLite hotel_places | 关键词评分检索的酒店候选 |
| `get_hotel_recommendations` | data.py HK_HOTELS | 按预算 / 区域过滤的结构化酒店方案 |
| `calculate_budget` | data.py BUDGET_TIERS | 人均 / 团体总费用明细 |
| `get_transport_info` | data.py TRANSPORT | 两区间交通方式 / 耗时 / 费用 |

### System Prompt 约束设计

System Prompt 包含 7 条路线规划规则：

| 规则 | 内容 |
|------|------|
| Rule 1 — 区域聚集 | 同日景点应在相同或相邻区域，减少来回奔波 |
| Rule 2 — 低预算优先 | 优先免费 / 低票价景点，MTR / 巴士 / 渡轮出行 |
| Rule 3 — 无障碍路线 | 带老人 / 儿童 / 孕妇时减少步行，优先无障碍景点 |
| Rule 4 — 节奏控制 | relaxed: 2 个活动 / 天；moderate: 3 个；packed: 4 个 |
| Rule 5 — 天气适应 | 高降雨 / 高湿度时优先室内或室内外混合景点 |
| Rule 6 — 避免拥挤 | 热门景点安排在非高峰时段，或替换为替代景点 |
| Rule 7 — 酒店区域推荐 | 根据多日活动分布、交通便利度、预算综合推荐住宿区域 |

> **"Tool-grounded only: do not fabricate attractions / hotels / restaurants / facts."**  
> 系统明确禁止 LLM 凭空捏造地点，所有内容必须来源于工具返回值。

---

## 5. 天气集成

天气数据采用双轨策略：

| 场景 | 数据源 | 字段 |
|------|--------|------|
| 出发日 ≤ 15 天内 | Open-Meteo `/v1/forecast` | 最高 / 最低温、降雨概率、WMO 天气码、湿度、UV 指数 |
| 出发日 > 15 天 | data.py 月均气候 + 每日变化量 | 月均温、月均湿度、月均UV、降雨概率、季节描述 |

天气数据由 `server.py` **独立获取**（绕过 LLM 输出），保证前端天气卡片字段结构稳定，不受模型输出格式波动影响。

---

## 6. 前端技术设计

### Map-first Studio（规划界面）

- 三栏布局：左侧偏好约束面板 · 中央 Leaflet 地图 · 右侧 Day 草案卡片
- 4 步引导式收集需求，每步支持自由文本补充
- 重新生成反馈输入框，高优先级约束注入 Agent

### Multi-view 结果展示

| 视图 | 内容 |
|------|------|
| Trip Summary Hero | 行程摘要卡片（天数 / 预算 / 人数 / 节奏） |
| Route Flow | 每日景点路线流 |
| Day-by-day Itinerary Cards | 逐日行程卡片（含天气信息） |
| Why This Plan | 行程逻辑解释（约束处理 / 区域聚集 / 预算匹配） |
| Full Itinerary | 完整 Markdown 文本 |

### 地图渲染（Leaflet.js）

后端返回 `attraction_coords`（景点名 → 经纬度字典）和行程文本中的 `map_data` JSON 块（每日景点名列表）。前端将景点名与坐标字典匹配，在 Leaflet 地图上绘制按日分色的 Marker 与折线路径。坐标数据来源于 `data.py` 中人工标注的 `lat` / `lng` 字段。

---

## 7. 设计亮点与权衡

### 设计亮点

- **天气独立获取**：`server.py` 直接调用 Open-Meteo，不依赖 LLM 格式化，保证前端数据稳定
- **MD5 增量更新**：RAG 数据库仅在 Excel 文件变更时重建，启动速度快
- **双入口设计**：Web（`server.py`）和 CLI（`app.py`）共享同一 Agent Pipeline
- **Regeneration Loop**：用户不满意时反馈直接注入为高优先级约束，无需重填表单
- **Tool-grounded 约束**：System Prompt 明确禁止 LLM 捏造地点，数据可信度有保障

### 技术权衡

- **Keyword RAG vs Embedding RAG**：牺牲语义泛化换取零额外依赖、快速部署
- **静态坐标数据**：景点坐标硬编码在 `data.py`，维护成本低但扩展需手动添加
- **单次 Agent 循环**：无多轮对话记忆，每次规划独立，简化状态管理
- **Flask 开发服务器**：生产环境需切换 Gunicorn，当前配置已预置 `Procfile`

---

*报告生成日期：2026-04-29*
