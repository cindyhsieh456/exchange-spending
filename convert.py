"""把 消費紀錄.xlsx 轉成網頁用的 data.js
用法:
  python convert.py              備註加密（會詢問密碼）→ 適合公開上傳
  python convert.py --no-notes   完全不含備註
  python convert.py --plain      備註明文（只留自己電腦用，不要上傳）
  python convert.py --password 你的密碼   （略過詢問，直接給密碼）
需要: pip install pandas openpyxl cryptography
"""
import sys, json, os, base64, hashlib, getpass, pandas as pd
A = sys.argv
MODE = "none" if "--no-notes" in A else "plain" if "--plain" in A else "enc"
# 補記的帳：日期, 類別, 備註, 金額, 是否可在網頁開關(1=可)
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
                     n=note.rsplit("/", 1)[0], a=abs(float(r["合計"])), p=pay(note)))
for d, c, n, a, o in EXTRA:
    rows.append(dict(d=d, c=c, n=n, a=a, p="估", e=1, **({"o": 1} if o else {})))
rows.sort(key=lambda x: x["d"], reverse=True)

data = dict(meta=dict(hasNotes=MODE == "plain"))
if MODE == "enc":
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    pw = A[A.index("--password") + 1] if "--password" in A else getpass.getpass("設定備註解鎖密碼: ")
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200000, 32)
    ct = AESGCM(key).encrypt(iv, json.dumps([r["n"] for r in rows], ensure_ascii=False).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    data["enc"] = dict(s=b(salt), i=b(iv), c=b(ct))
if MODE != "plain":
    for r in rows: r["n"] = ""
data["rows"] = rows
open("data.js", "w", encoding="utf-8").write(
    "window.DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
print(len(rows), "筆", round(sum(r["a"] for r in rows)), "元", "模式:", MODE)
