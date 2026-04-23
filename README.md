# HK Travel Planner

一个基于 AI Agent 的香港行程规划器，支持 **Map-first 规划体验**、多视图结果展示、天气注入、路线可视化，以及“不满意后追加要求重新生成”。

## Features

- **Map-first Planning Studio**
  - 三栏交互：左侧偏好约束、中间地图、右侧 Day 草案
  - 用户调整约束后，地图与草案同步刷新
- **Conversational + Visual UI**
  - 引导式收集需求（预算、节奏、兴趣、约束）
  - 每个步骤支持自由输入自定义要求
- **Multi-view Results**
  - Trip Summary Hero
  - Route Flow
  - Day-by-day itinerary cards
  - Why this plan works for you
  - Full itinerary（详细文本）
- **Weather Integration**
  - 近 15 天使用 Open-Meteo 实时预报
  - 更远日期使用季节气候估计
- **Regeneration Loop**
  - 结果页可输入“不满意的新要求”
  - 一键重新生成并作为高优先级约束
- **Dual Entry**
  - Web: `server.py`
  - CLI: `app.py`

## Tech Stack

- Python 3.10+
- Flask (Web API + static hosting)
- OpenAI Python SDK
- Requests
- python-dotenv
- Leaflet.js (frontend map rendering)

## Project Structure

```text
.
├── agent.py            # Agent pipeline + tool calls + itinerary generation
├── data.py             # Attractions/hotels/budget/transport/weather base data
├── server.py           # Flask API + frontend entry
├── app.py              # CLI interactive planner
├── static/
│   └── index.html      # Frontend (Map-first studio + result views)
├── requirements.txt
└── .env                # Local env vars (not committed)
```

## Quick Start

### 1) Install dependencies

```bash
pip install -r requirements.txt
pip install flask
```

### 2) Configure environment

Create `.env` in project root:

```env
OPENAI_API_KEY=your_api_key_here
```

### 3) Run Web App

```bash
python server.py
```

Open:

- [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 4) Run CLI version (optional)

```bash
python app.py
```

## API

### `POST /api/plan`

Request body (simplified):

```json
{
  "start_date": "2026-05-01",
  "days": 3,
  "budget": "medium",
  "pace": "moderate",
  "group_size": 2,
  "ages": [22],
  "interests": ["culture", "local_food"],
  "constraints": ["avoid_crowds"],
  "special": ["traveling_with_elderly"],
  "custom_requirements": {
    "step1_group_dates": "...",
    "step2_trip_shape": "...",
    "step3_travel_style": "...",
    "step4_constraints_route": "...",
    "regeneration_feedback": "..."
  }
}
```

Response includes:

- `itinerary` (LLM generated text + optional `map_data` block)
- `weather_data` (structured weather)
- `attraction_coords` (for map rendering)

## Notes

- 当前为开发服务器（Flask built-in），生产部署建议切换到 WSGI server。
- 若遇到天气不显示或路线流为空，前端已实现兜底解析逻辑，但仍建议保持模型输出格式稳定。

## License

For course/project use. Add your preferred license if needed.
