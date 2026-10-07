"""把 消費紀錄.xlsx 轉成網頁用的 data.js
用法: python convert.py            (保留備註)
      python convert.py --no-notes (公開版：備註完全不寫進檔案)
"""
import sys, json, pandas as pd
NO_NOTES = "--no-notes" in sys.argv
# 補記的帳（概估）：日期, 類別, 備註, 金額(正數)
# 第5欄 1 = 網頁上可開關（剛需、各人價格不同）
EXTRA = [("2026-01-05", "簽證+保險", "簽證與保險（概估）", 15000, 0),
         ("2025-09-29", "旅行", "台灣⇄布拉格來回機票（概估）", 32000, 1)]

def pay(note):
    for k in ("現金", "RV", "轉帳", "卡"):
        if k in note.split("/")[-1]:
            return k
    return "其他"

df = pd.read_excel("消費紀錄.xlsx").dropna(subset=["日期", "合計"])
rows = []
for _, r in df.iterrows():
    note = str(r["備註"])
    rows.append(dict(d=r["日期"].strftime("%Y-%m-%d"), c=r["類別"],
                     n="" if NO_NOTES else note.rsplit("/", 1)[0],
                     a=abs(float(r["合計"])), p=pay(note)))
for d, c, n, a, o in EXTRA:
    rows.append(dict(d=d, c=c, n="" if NO_NOTES else n, a=a, p="估", e=1, **({"o": 1} if o else {})))
rows.sort(key=lambda x: x["d"], reverse=True)
data = dict(meta=dict(hasNotes=not NO_NOTES), rows=rows)
open("data.js", "w", encoding="utf-8").write(
    "window.DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
print(len(rows), "筆", round(sum(r["a"] for r in rows)), "元", "(無備註)" if NO_NOTES else "")
