import json

from app.data.destinations import search_destinations
from app.data.hotels import get_hotels
from app.data.attractions import get_attractions
from app.data.weather import get_weather as get_weather_data

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_destinations",
            "description": "根据用户偏好搜索匹配的旅行目的地。根据关键词、兴趣和预算筛选目的地。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如 '海滩 亚洲'、'文化古城'、'蜜月'",
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "兴趣偏好列表，如 ['海滩', '美食', '文化', '冒险', '自然', '购物']",
                    },
                    "budget_level": {
                        "type": "string",
                        "enum": ["经济", "中等", "奢华"],
                        "description": "预算等级",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hotels",
            "description": "获取指定目的地的酒店住宿推荐。返回酒店名称、价格、评分和设施信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "目的地名称，如 '普吉岛'、'东京'",
                    },
                    "budget_level": {
                        "type": "string",
                        "enum": ["经济", "中等", "奢华"],
                        "description": "预算等级",
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "最低评分 (1.0-5.0)",
                    },
                },
                "required": ["destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attractions",
            "description": "获取指定目的地的景点和活动推荐。返回景点名称、类别、花费、时长和评分。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "目的地名称",
                    },
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["自然", "文化", "美食", "冒险", "购物"],
                        },
                        "description": "活动类别列表",
                    },
                },
                "required": ["destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定目的地和月份的天气信息。返回气温、湿度、降雨量和天气状况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "目的地名称",
                    },
                    "month": {
                        "type": "string",
                        "description": "月份，如 '1月'、'6月'、'December'",
                    },
                },
                "required": ["destination", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_travel_tips",
            "description": "获取旅行实用信息，包括签证要求、货币、语言和旅行建议。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "目的地名称",
                    },
                    "season": {
                        "type": "string",
                        "description": "旅行季节/月份，如 '12月'、'夏季'",
                    },
                },
                "required": ["destination"],
            },
        },
    },
]


def _get_travel_tips(destination: str, season: str | None = None) -> dict:
    """Get travel tips for a destination."""
    results = search_destinations(query=destination)
    if not results:
        return {"error": f"未找到 '{destination}' 的相关信息"}

    dest = results[0]
    tips = {
        "destination": dest["name"],
        "country": dest["country"],
        "language": dest["language"],
        "currency": dest["currency"],
        "visa_info": dest["visa_info"],
        "avg_daily_cost_usd": dest["avg_daily_cost_usd"],
        "best_seasons": dest["best_seasons"],
        "tips": [],
    }

    if dest["currency"] != "CNY":
        tips["tips"].append(f"当地使用{dest['currency']}，建议提前换汇或使用国际信用卡")
    if "落地签" in dest["visa_info"]:
        tips["tips"].append("落地签请准备好护照、照片和入境卡")
    elif "免签" in dest["visa_info"]:
        tips["tips"].append("免签入境，请确保护照有效期超过6个月")
    elif "签证" in dest["visa_info"]:
        tips["tips"].append("需要提前办理签证，建议至少提前1个月准备")
    if dest["avg_daily_cost_usd"] > 150:
        tips["tips"].append("该目的地消费较高，建议做好预算规划")
    else:
        tips["tips"].append(f"日均消费约{int(dest['avg_daily_cost_usd'])}美金，性价比不错")

    if season:
        weather = get_weather_data(destination, season)
        if weather:
            tips["weather_note"] = weather["travel_advice"]

    return tips


TOOL_EXECUTORS = {
    "search_destinations": lambda **kwargs: search_destinations(**kwargs),
    "get_hotels": lambda **kwargs: get_hotels(**kwargs),
    "get_attractions": lambda **kwargs: get_attractions(**kwargs),
    "get_weather": lambda **kwargs: get_weather_data(**kwargs),
    "get_travel_tips": lambda **kwargs: _get_travel_tips(**kwargs),
}


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return JSON string result."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)

    try:
        result = executor(**arguments)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
