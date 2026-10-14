"""把图片型 PDF 渲染成 PNG，便于人工/多模态查看。

运行：python scripts/render_pages.py
输出：data/raw/pages/<pdf名>_p<页>.png
"""
from __future__ import annotations

from pathlib import Path

import pymupdf  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD = ROOT / "manual_download"
OUT = ROOT / "data" / "raw" / "pages"
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = ["市场调研报告.pdf", "决策指南.pdf"]
DPI = 150


def render(name: str) -> None:
    doc = pymupdf.open(DOWNLOAD / name)
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=DPI)
        out = OUT / f"{name.replace('.pdf', '')}_p{i:02d}.png"
        pix.save(out)
    print(f"[render] {name}: {len(doc)} 页 -> {OUT}")


if __name__ == "__main__":
    for t in TARGETS:
        render(t)
