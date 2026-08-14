"""
Standalone PaddleOCR Adapter & Integration Engine.
Converts any version/shape of PaddleOCR raw result or SpatialOCRIndex into a validated List[OCRToken].
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

@dataclass
class OCRToken:
    id: int
    text: str
    normalized_text: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    x1: float
    y1: float
    x2: float
    y2: float
    center_x: float
    center_y: float
    line_id: Optional[int] = None
    region_id: Optional[int] = None
    auction_block_id: Optional[str] = None
    column_id: int = 0
    owner_auction_no: Optional[int] = None
    owner_locked: bool = False
    requires_resolution: bool = False
    source: str = "PaddleOCR"

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass

def parse_paddleocr_result(raw_result: Any) -> List[OCRToken]:
    """
    Robust adapter converting any PaddleOCR return format into List[OCRToken].
    Supports:
    1. List of OCRWordBox (SpatialOCRIndex.words)
    2. PaddleOCR v2/v3 list structure: [ [ [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, score)], ... ] ]
    3. PaddleOCR v4 dict structure: {"dt_polys": [...], "rec_text": [...], "rec_score": [...]}
    4. Simple list of dicts: [{"text": ..., "bbox": [...], "confidence": ...}]
    5. Plain string fallback with mock bounding boxes.
    """
    safe_print("\n============================================================")
    safe_print("========== OCR ADAPTER DEBUG ==========")
    safe_print("============================================================")

    res_type = type(raw_result).__name__
    res_len = len(raw_result) if hasattr(raw_result, "__len__") else 0
    safe_print(f"PADDLE OCR RESULT TYPE  : {res_type}")
    safe_print(f"PADDLE OCR RESULT LENGTH: {res_len}")

    tokens: List[OCRToken] = []
    dropped_count = 0
    malformed_count = 0

    if not raw_result:
        safe_print("Paddle boxes          : 0")
        safe_print("Paddle texts          : 0")
        safe_print("OCRToken objects      : 0")
        safe_print("STATUS                : FAIL (Empty result)")
        raise ValueError("OCR_ADAPTER_ERROR: Empty raw OCR result passed to adapter.")

    # 1. Handle SpatialOCRIndex or OCRWordBox list directly
    if isinstance(raw_result, list) and len(raw_result) > 0 and hasattr(raw_result[0], "text") and hasattr(raw_result[0], "x"):
        for idx, wb in enumerate(raw_result, start=1):
            txt = str(wb.text).strip()
            if not txt:
                dropped_count += 1
                continue
            x1, y1 = float(wb.x), float(wb.y)
            x2, y2 = x1 + float(wb.w), y1 + float(wb.h)
            tokens.append(OCRToken(
                id=idx,
                text=txt,
                normalized_text=txt,
                confidence=float(wb.confidence),
                bbox=(x1, y1, x2, y2),
                x1=x1, y1=y1, x2=x2, y2=y2,
                center_x=(x1 + x2) / 2.0,
                center_y=(y1 + y2) / 2.0,
                source="SpatialOCRIndex"
            ))

    # 2. Handle nested list formats: PaddleOCR `result` or `result[0]`
    elif isinstance(raw_result, list):
        items = raw_result
        if len(raw_result) > 0 and isinstance(raw_result[0], list) and len(raw_result[0]) > 0 and isinstance(raw_result[0][0], (list, tuple)):
            items = raw_result[0]

        tok_id = 1
        for item in items:
            text = ""
            conf = 0.90
            bbox = [0.0, 0.0, 50.0, 20.0]

            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
                conf = float(item.get("confidence", item.get("score", 0.90)))
                bbox = item.get("bbox", [0, 0, 50, 20])
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                pts, txt_conf = item[0], item[1]
                if isinstance(pts, (list, tuple)) and len(pts) >= 4:
                    xs = [float(p[0]) for p in pts]
                    ys = [float(p[1]) for p in pts]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]
                elif isinstance(pts, (list, tuple)) and len(pts) == 4 and all(isinstance(v, (int, float)) for v in pts):
                    bbox = [float(v) for v in pts]

                if isinstance(txt_conf, (list, tuple)) and len(txt_conf) >= 2:
                    text = str(txt_conf[0]).strip()
                    conf = float(txt_conf[1])
                else:
                    text = str(txt_conf).strip()
            else:
                malformed_count += 1
                continue

            if not text:
                dropped_count += 1
                continue

            x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
            if x2 < x1: x1, x2 = x2, x1
            if y2 < y1: y1, y2 = y2, y1

            tokens.append(OCRToken(
                id=tok_id,
                text=text,
                normalized_text=text,
                confidence=conf,
                bbox=(x1, y1, x2, y2),
                x1=x1, y1=y1, x2=x2, y2=y2,
                center_x=(x1 + x2) / 2.0,
                center_y=(y1 + y2) / 2.0,
                source="PaddleOCR"
            ))
            tok_id += 1

    # 3. Handle Dictionary structures (v4 dict results)
    elif isinstance(raw_result, dict):
        texts = raw_result.get("rec_text") or raw_result.get("texts") or []
        scores = raw_result.get("rec_score") or raw_result.get("scores") or [0.90] * len(texts)
        boxes = raw_result.get("dt_polys") or raw_result.get("boxes") or []

        tok_id = 1
        for i in range(min(len(texts), len(boxes))):
            txt = str(texts[i]).strip()
            conf = float(scores[i]) if i < len(scores) else 0.90
            pts = boxes[i]
            if not txt:
                dropped_count += 1
                continue
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            tokens.append(OCRToken(
                id=tok_id,
                text=txt,
                normalized_text=txt,
                confidence=conf,
                bbox=(x1, y1, x2, y2),
                x1=x1, y1=y1, x2=x2, y2=y2,
                center_x=(x1 + x2) / 2.0,
                center_y=(y1 + y2) / 2.0,
                source="PaddleOCR"
            ))
            tok_id += 1

    # 4. Handle Plain String fallback
    elif isinstance(raw_result, str):
        lines = raw_result.splitlines()
        curr_y = 50.0
        tok_id = 1
        for l in lines:
            words = l.split()
            curr_x = 50.0
            for w in words:
                x1, y1 = curr_x, curr_y
                x2, y2 = curr_x + len(w) * 10, curr_y + 20
                tokens.append(OCRToken(
                    id=tok_id,
                    text=w,
                    normalized_text=w,
                    confidence=0.95,
                    bbox=(x1, y1, x2, y2),
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    center_x=(x1 + x2) / 2.0,
                    center_y=(y1 + y2) / 2.0,
                    source="PlainTextFallback"
                ))
                curr_x += len(w) * 10 + 5
                tok_id += 1
            curr_y += 25.0

    safe_print(f"Paddle boxes          : {len(tokens) + dropped_count}")
    safe_print(f"Paddle texts          : {len(tokens) + dropped_count}")
    safe_print(f"OCRToken objects      : {len(tokens)}")
    safe_print(f"Dropped tokens        : {dropped_count}")
    safe_print(f"Malformed tokens      : {malformed_count}")

    if len(tokens) == 0:
        safe_print("STATUS                : FAIL (0 OCR tokens created)")
        raise ValueError(f"OCR_ADAPTER_ERROR: Adapter parsed {res_len} raw items but produced 0 valid OCRTokens.")

    safe_print("STATUS                : PASS")
    safe_print("============================================================\n")
    return tokens
