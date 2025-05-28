from dataclasses import dataclass
from typing import List


@dataclass
class AnalysisData:
    """Container for analysis results"""
    product_info: str
    image_urls: List[str]
    image_analysis: str 