"""
Document Object Builder for PDF Processing Pipeline.
Reconstructs PDF pages into physical layout grids (Rows, Columns, Cells, Bounding Boxes).
"""

from __future__ import annotations
import fitz  # PyMuPDF
from app.core.logger import get_logger

logger = get_logger(__name__)

class DocumentObjectBuilder:
    """
    Builds a Cell-Based Document Model reconstructing table rows, columns, and cells.
    """

    PADDING = {"left": -5, "right": 5, "top": -2, "bottom": 2}

    def build_from_pdf(self, pdf_path: str, ocr_service=None) -> dict:
        """
        Extract coordinate-aware page blocks, reconstruct physical table grid (Rows, Columns, Cells).
        """
        doc_obj = {
            "pdf_path": pdf_path,
            "total_pages": 0,
            "full_text": "",
            "pages": [],
            "metadata": {},
            "sections": {}
        }

        try:
            doc = fitz.open(pdf_path)
            doc_obj["total_pages"] = len(doc)
            doc_obj["metadata"] = doc.metadata or {}

            full_text_lines = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_dict = page.get_text("dict")
                page_text = page.get_text("text") or ""

                spans_list = []
                for block in page_dict.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                stext = span.get("text", "")
                                if not stext.strip():
                                    continue
                                bbox = list(span.get("bbox", []))
                                # Expand cell boundary by padding
                                expanded_bbox = [
                                    bbox[0] + self.PADDING["left"],
                                    bbox[1] + self.PADDING["top"],
                                    bbox[2] + self.PADDING["right"],
                                    bbox[3] + self.PADDING["bottom"]
                                ]
                                spans_list.append({
                                    "text": stext,
                                    "bbox": bbox,
                                    "expanded_bbox": expanded_bbox,
                                    "font": span.get("font"),
                                    "size": span.get("size")
                                })

                # Y-coordinate Row Clustering (tolerance: 4px)
                spans_sorted_y = sorted(spans_list, key=lambda s: (s["bbox"][1], s["bbox"][0]))
                rows_list = []
                current_row_spans = []
                current_y = None

                for s in spans_sorted_y:
                    y_center = (s["bbox"][1] + s["bbox"][3]) / 2.0
                    if current_y is None:
                        current_y = y_center
                        current_row_spans.append(s)
                    elif abs(y_center - current_y) <= 6.0:
                        current_row_spans.append(s)
                    else:
                        # Finalize current row
                        row_spans_sorted_x = sorted(current_row_spans, key=lambda s: s["bbox"][0])
                        row_text = " ".join([sp["text"].strip() for sp in row_spans_sorted_x if sp["text"].strip()])
                        min_x0 = min(sp["bbox"][0] for sp in row_spans_sorted_x)
                        min_y0 = min(sp["bbox"][1] for sp in row_spans_sorted_x)
                        max_x1 = max(sp["bbox"][2] for sp in row_spans_sorted_x)
                        max_y1 = max(sp["bbox"][3] for sp in row_spans_sorted_x)

                        # Build Cells for row by X-coordinate clustering
                        cells_in_row = []
                        col_idx = 1
                        for sp in row_spans_sorted_x:
                            cells_in_row.append({
                                "cell_id": f"r{len(rows_list)+1}_c{col_idx}",
                                "row": len(rows_list) + 1,
                                "column": col_idx,
                                "bbox": sp["bbox"],
                                "expanded_bbox": sp["expanded_bbox"],
                                "text": sp["text"].strip()
                            })
                            col_idx += 1

                        rows_list.append({
                            "row_index": len(rows_list) + 1,
                            "bbox": [min_x0, min_y0, max_x1, max_y1],
                            "text": row_text,
                            "spans": row_spans_sorted_x,
                            "cells": cells_in_row
                        })

                        current_y = y_center
                        current_row_spans = [s]

                if current_row_spans:
                    row_spans_sorted_x = sorted(current_row_spans, key=lambda s: s["bbox"][0])
                    row_text = " ".join([sp["text"].strip() for sp in row_spans_sorted_x if sp["text"].strip()])
                    min_x0 = min(sp["bbox"][0] for sp in row_spans_sorted_x)
                    min_y0 = min(sp["bbox"][1] for sp in row_spans_sorted_x)
                    max_x1 = max(sp["bbox"][2] for sp in row_spans_sorted_x)
                    max_y1 = max(sp["bbox"][3] for sp in row_spans_sorted_x)

                    cells_in_row = []
                    col_idx = 1
                    for sp in row_spans_sorted_x:
                        cells_in_row.append({
                            "cell_id": f"r{len(rows_list)+1}_c{col_idx}",
                            "row": len(rows_list) + 1,
                            "column": col_idx,
                            "bbox": sp["bbox"],
                            "expanded_bbox": sp["expanded_bbox"],
                            "text": sp["text"].strip()
                        })
                        col_idx += 1

                    rows_list.append({
                        "row_index": len(rows_list) + 1,
                        "bbox": [min_x0, min_y0, max_x1, max_y1],
                        "text": row_text,
                        "spans": row_spans_sorted_x,
                        "cells": cells_in_row
                    })

                # Check text layer quality
                if len(page_text.strip()) < 50 and ocr_service:
                    logger.info("Page %d has sparse text layer. Triggering OCR fallback...", page_num + 1)
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    try:
                        ocr_result = ocr_service.extract_text_from_bytes(img_bytes)
                        if ocr_result and len(ocr_result.strip()) > len(page_text.strip()):
                            page_text = ocr_result
                    except Exception as exc:
                        logger.warning("OCR fallback on page %d failed: %s", page_num + 1, exc)

                full_text_lines.append(page_text)
                doc_obj["pages"].append({
                    "page_number": page_num + 1,
                    "bbox": [0, 0, page.rect.width, page.rect.height],
                    "text": page_text,
                    "rows": rows_list,
                    "lines": [ln.strip() for ln in page_text.splitlines() if ln.strip()]
                })

            doc_obj["full_text"] = "\n".join(full_text_lines)
            logger.info("Cell-Based Document Model built successfully across %d pages (%d total rows reconstructed).",
                        len(doc_obj["pages"]), sum(len(p["rows"]) for p in doc_obj["pages"]))

        except Exception as exc:
            logger.exception("Failed to build Cell-Based Document Model from PDF %s: %s", pdf_path, exc)

        return doc_obj
