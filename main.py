import aiohttp
from astrbot.api.all import *
from astrbot.api.message_components import Image

@register(
    name="serpapi_lens",
    author="YourName",
    version="1.0.0",
    description="使用 SerpApi 进行 Google Lens 视觉以图搜图"
)
class SerpApiLensPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}

    @llm_tool(name="google_lens_search")
    async def google_lens_search(self, event: AstrMessageEvent) -> str:
        """当用户发送图片询问图中的人物是谁、物品型号、动植物品种或要求以图搜图时，调用此工具进行 Google Lens 视觉检索。"""
        api_key = self.config.get("api_key", "").strip()
        if not api_key:
            return "错误：未配置 SerpApi API Key。"

        # 从消息组件中提取图片 URL
        image_url = None
        for comp in event.message_obj.message:
            if isinstance(comp, Image):
                # 优先获取图片的公网 URL
                image_url = getattr(comp, "url", None) or getattr(comp, "path", None)
                break

        if not image_url:
            return "错误：未在当前消息中检测到图片，无法执行 Google Lens 搜索。"

        # 请求 SerpApi 的 Google Lens 引擎
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": api_key,
            "hl": "zh-cn"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://serpapi.com/search", params=params, timeout=20) as resp:
                    if resp.status != 200:
                        return f"Google Lens 搜索失败，HTTP 状态码: {resp.status}"
                    data = await resp.json()

            results = []
            
            # 1. 提取核心视觉匹配（Visual Matches）
            visual_matches = data.get("visual_matches", [])[:4]
            for match in visual_matches:
                title = match.get("title", "")
                source = match.get("source", "")
                link = match.get("link", "")
                results.append(f"匹配标题: {title}\n来源: {source}\n参考链接: {link}")

            # 2. 提取知识图谱/标签（Knowledge Graph / Tags）
            knowledge_graph = data.get("knowledge_graph", {})
            if knowledge_graph:
                kg_title = knowledge_graph.get("title", "")
                kg_type = knowledge_graph.get("type", "")
                results.insert(0, f"识别实体: {kg_title} ({kg_type})")

            if not results:
                return "Google Lens 未找到高相似度的匹配结果。"

            return "\n\n".join(results)

        except Exception as e:
            return f"执行视觉搜索时发生异常: {str(e)}"
