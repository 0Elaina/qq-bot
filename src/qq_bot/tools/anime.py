import asyncio
from urllib.parse import quote

from httpx import AsyncClient
from langchain_core.tools import tool

# Bangumi API 搜索端点与官方条目基础 URL
_BANGUMI_SEARCH_URL = "https://api.bgm.tv/v0/search/subjects"
_BANGUMI_SUBJECT_URL = "https://bgm.tv/subject/{subject_id}"

# B 站直达搜索页 URL 模板（支持直接唤起客户端或网页端）
_BILIBILI_SEARCH_URL = "https://search.bilibili.com/all?keyword={keyword}"

# Bangumi 规范要求必须提供合理的 User-Agent，否则会被 403 拦截
_HEADERS = {
    "User-Agent": "qq-bot/1.0 (https://github.com/0Elaina/qq-bot)",
    "Content-Type": "application/json",
}

# Bangumi 条目类型枚举：2 代表动画（Anime）
_SUBJECT_TYPE_ANIME = 2


def _format_subject_card(subject: dict) -> str:
    """提取单个条目核心信息并拼接双链接卡片"""
    title = subject.get("name_cn") or subject.get("name") or "未知片名"
    score = subject.get("score") or "暂无评分"
    raw_summary = (subject.get("summary") or "暂无简介").strip()
    summary = raw_summary[:80] + "..." if len(raw_summary) > 80 else raw_summary

    bgm_link = _BANGUMI_SUBJECT_URL.format(subject_id=subject.get("id"))
    bili_link = _BILIBILI_SEARCH_URL.format(keyword=quote(title))

    return (
        f"📺【{title}】(评分: {score})\n"
        f"📝 简介: {summary}\n"
        f"🔗 播放: {bili_link}\n"
        f"📖 条目: {bgm_link}"
    )


async def _fetch_subjects(
    client: AsyncClient,
    keyword: str = "",
    air_date: list[str] = [],
    tags: list[str] = [],
    sort: str = "rank",
    limit: int = 3,
) -> list[dict]:
    """向 Bangumi 异步检索条目，支持 keyword、air_date、tags 与 sort 纯透传"""
    payload = {
        "keyword": keyword or "动画",
        "sort": sort,
        "filter": {
            "type": [_SUBJECT_TYPE_ANIME],
            **({"air_date": air_date} if air_date else {}),
            **({"tag": tags} if tags else {}),
        },
        "limit": limit,
    }
    response = await client.post(
        _BANGUMI_SEARCH_URL, json=payload, headers=_HEADERS, timeout=6.0
    )
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get("data", [])


@tool
async def recommend_anime(
    titles: list[str] = [],
    keyword: str = "",
    air_date: list[str] = [],
    tags: list[str] = [],
    sort: str = "rank",
) -> str:
    """查询番剧真实评分、简介以及 B 站观看搜索直达链接。

    使用契约：
    1. 针对用户的任何喜好、年代或情绪需求，优先由你运用动漫常识推选 1~3 部最契合作品名称，传入 titles 并发验真；
    2. 亦可直接传入 keyword（关键词）、air_date（如 [">=2024-01-01"]）、tags（如 ["机战"]）、sort（"heat" 热门 / "rank" 高分）进行条件检索；
    3. 若用户需求模糊，不要盲目调用本工具，请先在对话中与用户自然交流明确喜好。
    """
    cleaned_titles = [t.strip() for t in titles if t.strip()]
    if not cleaned_titles and not keyword.strip() and not air_date and not tags:
        return "未提供候选片名或检索条件。请先与用户自然交流明确其喜好，或由你推选出具体候选片名后再调用本工具。"
    subjects = []
    try:
        async with AsyncClient() as client:
            if cleaned_titles:
                tasks = [
                    _fetch_subjects(client, keyword=t, limit=1) for t in cleaned_titles
                ]
                results = await asyncio.gather(*tasks)
                subjects = [res[0] for res in results if res]
            else:
                subjects = await _fetch_subjects(
                    client,
                    keyword=keyword.strip(),
                    air_date=air_date,
                    tags=tags,
                    sort=sort,
                    limit=3,
                )
    except Exception:
        return "联网查询番剧失败（网络超时）。可向用户说明网络状况并提供通用推荐。"

    if not subjects:
        return "未检索到匹配的番剧条目。可告知用户未检索到结果并提供备选推荐。"

    cards = [_format_subject_card(s) for s in subjects]
    return (
        "已检索到以下番剧条目（请向用户汇报并务必完整保留以下信息和链接）：\n\n"
        + "\n\n".join(cards)
    )
