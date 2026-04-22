"""并行多模态处理器"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
from wordparser.multimodal.parser import MultimodalParser, MultimodalResult


class ParallelMultimodalProcessor:
    """并行多模态内容处理器

    使用线程池并行处理多个多模态内容解析任务。
    """

    def __init__(self, max_workers: int = 4):
        """初始化并行处理器

        Args:
            max_workers: 最大线程数，默认为4
        """
        self.max_workers = max_workers
        self.parser = MultimodalParser()

    def process_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[MultimodalResult]:
        """批量处理多模态内容

        Args:
            items: 待处理的项目列表，每个项目是包含type和data的字典
                   - type: 内容类型 ('table', 'image', 'chart', 'smartart')
                   - data: 对应类型的原始数据

        Returns:
            List[MultimodalResult]: 解析结果列表，顺序与输入一致

        Example:
            >>> processor = ParallelMultimodalProcessor()
            >>> items = [
            ...     {'type': 'table', 'data': '<w:tbl>...</w:tbl>'},
            ...     {'type': 'image', 'data': {'format': 'png', 'width': 800, 'height': 600, 'data': b'...'}}
            ... ]
            >>> results = processor.process_batch(items)
        """
        results = [None] * len(items)

        # 创建任务映射
        def process_item(index: int, item: Dict[str, Any]) -> tuple:
            """处理单个项目

            Returns:
                tuple: (index, MultimodalResult)
            """
            content_type = item.get('type')
            data = item.get('data')

            if content_type == 'table':
                result = self.parser.parse_table(data)
            elif content_type == 'image':
                result = self.parser.parse_image(data)
            elif content_type == 'chart':
                result = self.parser.parse_chart(data)
            elif content_type == 'smartart':
                result = self.parser.parse_smartart(data)
            else:
                result = MultimodalResult(
                    content=f"*未知类型: {content_type}*",
                    confidence=0.0,
                    metadata={
                        "type": "error",
                        "error_type": "unknown_content_type",
                        "provided_type": content_type
                    }
                )

            return (index, result)

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(process_item, i, item): i
                for i, item in enumerate(items)
            }

            # 收集结果
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
            List[MultimodalResult]: 解析结果列表
        """
        results = []

        def process_item_with_callback(index: int, item: Dict[str, Any]) -> MultimodalResult:
            """处理单个项目并调用回调"""
            content_type = item.get('type')
            data = item.get('data')

            if content_type == 'table':
                result = self.parser.parse_table(data)
            elif content_type == 'image':
                result = self.parser.parse_image(data)
            elif content_type == 'chart':
                result = self.parser.parse_chart(data)
            elif content_type == 'smartart':
                result = self.parser.parse_smartart(data)
            else:
                result = MultimodalResult(
                    content=f"*未知类型: {content_type}*",
                    confidence=0.0,
                    metadata={
                        "type": "error",
                        "error_type": "unknown_content_type",
                        "provided_type": content_type
                    }
                )

            # 调用回调函数
            callback(index, result)
            return result

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(process_item_with_callback, i, item)
                for i, item in enumerate(items)
            ]

            # 等待所有任务完成并收集结果
            for future in as_completed(futures):
                results.append(future.result())

        # 按原始顺序排序
        results.sort(key=lambda x: items.index(next(
            item for item in items
            if item.get('type') in ['table', 'image', 'chart', 'smartart']
        )))

        return results
