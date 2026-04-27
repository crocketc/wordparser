"""并行多模态处理器

⚠️ 技术债务: 该类当前未被实际使用

现状:
    parser.py 直接使用 ThreadPoolExecutor 实现并行处理，
    未通过此类进行统一封装。

原因分析:
    1. 各类内容（图片/表格/Chart/SmartArt）处理逻辑差异较大
    2. 统一接口反而增加抽象层复杂度
    3. 直接使用 ThreadPoolExecutor 代码更简洁

决策点:
    待评估未来是否需要统一并行处理接口。
    如果未来需要在多个模块复用并行逻辑，可考虑集成此类。
    否则建议删除以降低维护成本。

跟踪:
    记录日期: 2026-04-27
    文档: docs/lessons-learned.md (技术债务章节)
"""

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
        """批量处理多模态内容（滑动窗口模式）

        优化策略：批量提交 + 动态补充，避免一次性创建大量Future对象

        Args:
            items: 待处理的项目列表，每个项目是包含type和data的字典

        Returns:
            List[MultimodalResult]: 解析结果列表，顺序与输入一致
        """
        if not items:
            return []

        results = [None] * len(items)
        pending_indices = iter(range(len(items)))

        def process_item(index: int) -> tuple:
            item = items[index]
            content_type = item.get('type')
            data = item.get('data')
            result = self._parse_item(content_type, data)
            return (index, result)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 初始提交：填满线程池
            pending_futures = {}
            for _ in range(min(self.max_workers, len(items))):
                idx = next(pending_indices, None)
                if idx is not None:
                    future = executor.submit(process_item, idx)
                    pending_futures[future] = idx

            # 动态补充：完成一个，提交一个
            while pending_futures:
                # 等待任意一个任务完成
                completed = next(as_completed(pending_futures))
                idx = pending_futures.pop(completed)
                index, result = completed.result()
                results[index] = result

                # 立即补充下一个任务（如果还有）
                next_idx = next(pending_indices, None)
                if next_idx is not None:
                    new_future = executor.submit(process_item, next_idx)
                    pending_futures[new_future] = next_idx

        return results

    def process_batch_with_callback(
        self,
        items: List[Dict[str, Any]],
        callback: Callable[[int, MultimodalResult], None]
    ) -> List[MultimodalResult]:
        """批量处理多模态内容，带回调函数（滑动窗口模式）

        优化策略：批量提交 + 动态补充，避免一次性创建大量Future对象

        Args:
            items: 待处理的项目列表
            callback: 回调函数，接收 (index, result) 参数

        Returns:
            List[MultimodalResult]: 解析结果列表，顺序与输入一致
        """
        if not items:
            return []

        results = [None] * len(items)
        pending_indices = iter(range(len(items)))

        def process_item_with_callback(index: int) -> tuple:
            item = items[index]
            content_type = item.get('type')
            data = item.get('data')
            result = self._parse_item(content_type, data)
            callback(index, result)
            return (index, result)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 初始提交：填满线程池
            pending_futures = {}
            for _ in range(min(self.max_workers, len(items))):
                idx = next(pending_indices, None)
                if idx is not None:
                    future = executor.submit(process_item_with_callback, idx)
                    pending_futures[future] = idx

            # 动态补充：完成一个，提交一个
            while pending_futures:
                # 等待任意一个任务完成
                completed = next(as_completed(pending_futures))
                idx = pending_futures.pop(completed)
                index, result = completed.result()
                results[index] = result

                # 立即补充下一个任务（如果还有）
                next_idx = next(pending_indices, None)
                if next_idx is not None:
                    new_future = executor.submit(process_item_with_callback, next_idx)
                    pending_futures[new_future] = next_idx

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
