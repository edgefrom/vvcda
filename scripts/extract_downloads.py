"""提取 manual_download/ 里的文件为可读文本，便于解析与转写。

运行：python scripts/extract_downloads.py
输出：data/raw/*.txt / *.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import fitz  # PyMuPDF  # noqa: E402
import pandas as pd  # noqa: E402

DOWNLOAD = ROOT / "manual_download"
OUT = ROOT / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


def extract_pdf(name: str) -> None:
    path = DOWNLOAD / name
    doc = fitz.open(path)
    parts: list[str] = []
    for i, page in enumerate(doc, 1):
        parts.append(f"===== 第 {i} 页 =====\n{page.get_text()}")
    text = "\n".join(parts)
    out = OUT / (name.replace(".pdf", ".txt"))
    out.write_text(text, encoding="utf-8")
    print(f"[PDF] {name}: {len(doc)} 页, {len(text)} 字符 -> {out.name}")


def extract_xls(name: str) -> None:
    path = DOWNLOAD / name
    raw = path.read_bytes()[:8]
    print(f"[XLS] {name} 头部: {raw!r}")
    try:
        df = pd.read_excel(path, sheet_name=None)
    except Exception as exc:  # noqa: BLE001
        print(f"[XLS] 读取失败: {exc}")
        return
    for sheet, data in df.items():
        out = OUT / f"{name.replace('.xls', '')}_{sheet}.csv"
        data.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"[XLS] sheet={sheet!r}: shape={data.shape} -> {out.name}")
        print(data.head(20).to_string())


def main() -> None:
    for pdf in ["市场调研报告.pdf", "案例背景.pdf", "决策指南.pdf"]:
        try:
            extract_pdf(pdf)
        except Exception as exc:  # noqa: BLE001
            print(f"[PDF] {pdf} 失败: {exc}")
    extract_xls("results-ir00.xls")


if __name__ == "__main__":
    main()
