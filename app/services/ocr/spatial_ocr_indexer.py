"""
Spatial OCR Indexer and Centralized Cache.

Provides single-pass OCR execution with spatial caching.
Downstream pipeline stages query this index by bounding box coordinates without invoking PaddleOCR again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class OCRWordBox:
    box: List[List[float]]
    text: str
    confidence: float
    x: float
    y: float
    w: float
    h: float

class SpatialOCRIndex:
    """
    Spatial OCR Index representing a single-pass OCR scan over a document page.
    """

    def __init__(self, raw_lines: List[Any]) -> None:
        self.raw_lines = raw_lines
        self.words: List[OCRWordBox] = []
        self.full_text_lines: List[str] = []
        self._build_index(raw_lines)

    def _build_index(self, raw_lines: List[Any]) -> None:
        if not raw_lines:
            return

        lines_list = raw_lines[0] if isinstance(raw_lines, list) and len(raw_lines) > 0 and isinstance(raw_lines[0], list) else raw_lines

        for item in lines_list:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue

            box = item[0]
            txt_conf = item[1]

            if not isinstance(txt_conf, (list, tuple)) or len(txt_conf) < 2:
                text = str(txt_conf)
                conf = 0.95
            else:
                text = str(txt_conf[0]).strip()
                conf = float(txt_conf[1])

            if not text:
                continue

            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            w = max_x - min_x
            h = max_y - min_y

            self.words.append(
                OCRWordBox(
                    box=box,
                    text=text,
                    confidence=conf,
                    x=min_x,
                    y=min_y,
                    w=w,
                    h=h,
                )
            )
            self.full_text_lines.append(text)

        # Sort words in standard reading order (Top-to-Bottom, Left-to-Right)
        self.words.sort(key=lambda item: (round(item.y / 20.0) * 20.0, item.x))

    def get_full_text(self) -> str:
        """Return full document text extracted in reading order."""
        return "\n".join(self.full_text_lines)

    def query_bounding_box(self, x: float, y: float, w: float, h: float, margin: float = 10.0) -> str:
        """
        Query cached OCR text lying within a bounding box (x, y, w, h).
        Executing this avoids re-running PaddleOCR for sub-crops.
        """
        x1, y1 = x - margin, y - margin
        x2, y2 = x + w + margin, y + h + margin

        matching_words: List[OCRWordBox] = []
        for word in self.words:
            if (x1 <= word.x <= x2 or x1 <= word.x + word.w <= x2) and \
               (y1 <= word.y <= y2 or y1 <= word.y + word.h <= y2):
                matching_words.append(word)

        matching_words.sort(key=lambda item: (round(item.y / 20.0) * 20.0, item.x))
        return "\n".join(w.text for w in matching_words)

class SpatialOCRIndexCache:
    """
    Centralized SHA-256 in-memory OCR cache for SpatialOCRIndex objects.
    Guarantees OCR is invoked strictly ONCE per image/page file.
    """

    _cache: Dict[str, SpatialOCRIndex] = {}

    @classmethod
    def compute_hash(cls, image_path: Path | str) -> str:
        p = Path(image_path)
        if not p.exists():
            return str(image_path)
        try:
            with open(p, "rb") as f:
                return hashlib.sha256(f.read()[:65536]).hexdigest()
        except Exception:
            return str(image_path)

    @classmethod
    def get(cls, image_path: Path | str) -> Optional[SpatialOCRIndex]:
        key = cls.compute_hash(image_path)
        return cls._cache.get(key)

    @classmethod
    def put(cls, image_path: Path | str, raw_ocr_result: List[Any]) -> SpatialOCRIndex:
        key = cls.compute_hash(image_path)
        idx = SpatialOCRIndex(raw_ocr_result)
        cls._cache[key] = idx
        return idx
