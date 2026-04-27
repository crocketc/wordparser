"""并行多模态处理器"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
from wordparser.multimodal.parser import MultimodalParser, MultimodalResult


class ParallelMultimodalProcessor:
    """并行多模态内容处理器

    使用线程池并行处理多个多模态内容解析任务。
    """

    def __init__(
        self,
        max_workers: int = 4,
        vision_client=None,
        renderer=None,
        enable_render_fallback: bool = True,
    ):
        """初始化并行处理器

        Args:
            max_workers: 最大线程数，默认为4
            vision_client: 视觉客户端实例
            renderer: 文档渲染器实例
            enable_render_fallback: 是否启用渲染降级
        """
        self.max_workers = max_workers
        self.parser = MultimodalParser(
            vision_client=vision_client,
            renderer=renderer,
            enable_render_fallback=enable_render_fallback,
        )

    def process_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[MultimodalResult]:
        """批量处理多模态内容

        Args:
            items: 待处理的项目列表，每个项目是包含type和data的字典

        Returns:
            List[MultimodalResult]: 解析结果列表，顺序与输入一致
        """
        results = [None] * len(items)

        def process_item(index: int, item: Dict[str, Any]) -> tuple:
            content_type = item.get('type')
            data = item.get('data')
            result = self._parse_item(content_type, data)
            return (index, result)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(process_item, i, item): i
                for i, item in enumerate(items)
            }
            for future in as_completed(future_to_index):
                index, result = future.result()
                results[index] = result

        return results

    def process_batch_with_callback(
        self,
        items: List[Dict[str, Any]],
        callback: Callable[[int, MultimodalResult], None]
    ) -> List[MultimodalResult]:
        """批量处理多模态内容，带回调函数

        Args:
            items: 待处理的项目列表
            callback: 回调函数，接收 (index, result) 参数

        Returns:
            List[MultimodalResult]: 解析结果列表，顺序与输入一致
        """
        results = [None] * len(items)

        def process_item_with_callback(index: int, item: Dict[str, Any]) -> tuple:
            content_type = item.get('type')
            data = item.get('data')
            result = self._parse_item(content_type, data)
            callback(index, result)
            return index, result

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(process_item_with_callback, i, item): i
                for i, item in enumerate(items)
            }
            for future in as_completed(future_to_index):
                index, result = future.result()
                results[index] = result

        return results

    def _parse_item(self, content_type: Optional[str], data: Any) -> MultimodalResult:
        """解析单个内容项"""
        if content_type == 'table':
            return self.parser.parse_complex_table(data)
        elif content_type == 'image':
            return self.parser.parse_image(data)
        elif content_type == 'chart':
            return self.parser.parse_chart_with_data(data)
        elif content_type == 'smartart':
            return self.parser.parse_smartart_with_data(data)
        else:
            return MultimodalResult(
                content=f"*未知类型: {content_type}*",
                confidence=0.0,
                metadata={
                    "type": "error",
                    "error_type": "unknown_content_type",
                    "provided_type": content_type,
                },
            )
