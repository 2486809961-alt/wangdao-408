#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wd408.py — 408 王道四本书的考点检索（PDF 页 + 原书页，双标注）

相比 cite.py 的优势：王道四本书印张偏移统一为 12（已核对 p60→p48、p282→p270），
不依赖页脚数字猜测，页码永远准。

用法:
  python3 wd408.py "折半查找 判定树" -k 5
  python3 wd408.py "快表" --book 操作系统 -k 3
  python3 wd408.py "六状态 图" --book 数据结构 --page 268      # 取整页原文
  python3 wd408.py "TCP 拥塞控制" --json                       # 给 note.py 用
"""
import argparse, json, os, re, sqlite3, sys

DB = "/Users/jiarun/.dsh/skills/obsidian-exam-recap/index/kb.db"
VAULT = "/Users/jiarun/Documents/王道408"
OFFSET = 12
BOOKS = {"数据结构": "27王道《数据结构》", "计算机组成原理": "27王道《计算机组成原理》",
         "操作系统": "王道2027操作系统", "计算机网络": "27王道《计算机网络》"}


def con():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA busy_timeout=60000")
    return c


ALIAS = {"计组": "计算机组成原理", "机组": "计算机组成原理", "组成": "计算机组成原理",
         "os": "操作系统", "OS": "操作系统", "计网": "计算机网络", "网络": "计算机网络",
         "ds": "数据结构", "DS": "数据结构", "ds ": "数据结构"}


def docs(c, book):
    book = ALIAS.get(book, book)
    rows = c.execute("SELECT id,path,title,locs FROM docs WHERE kind='pdf' AND vault='王道408'").fetchall()
    out = []
    for r in rows:
        if book and book not in os.path.basename(r[1]):
            continue
        out.append(r)
    return out


def subj_of(title):
    for k, v in BOOKS.items():
        if v in title or k in title:
            return k
    return title


def search(terms, book, k):
    c = con()
    hits = []
    for did, path, title, locs in docs(c, book):
        for loc, text in c.execute("SELECT loc,text FROM chunks WHERE doc_id=?", (did,)):
            low = text.lower()
            score = sum(len(t) ** 1.5 * low.count(t.lower()) for t in terms if t.lower() in low)
            if score:
                hits.append({"book": subj_of(title), "path": path, "pdf_page": int(loc[1:]),
                             "printed": int(loc[1:]) - OFFSET, "score": round(score, 1), "text": text})
    hits.sort(key=lambda h: -h["score"])
    return hits[:k]


def snippet(text, terms, width=300):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not re.fullmatch(r"\d{1,4}", ln)]
    body = " ".join(lines)
    pos = -1
    for t in terms:
        p = body.lower().find(t.lower())
        if p >= 0:
            pos = p
            break
    if pos < 0:
        return body[:width]
    a = max(0, pos - width // 3)
    return ("…" if a else "") + body[a:a + width] + "…"


def page_text(book, page):
    c = con()
    for did, path, title, locs in docs(c, book):
        row = c.execute("SELECT text FROM chunks WHERE doc_id=? AND loc=?", (did, f"p{page}")).fetchone()
        if row:
            return {"book": subj_of(title), "pdf_page": page, "printed": page - OFFSET, "text": row[0]}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="*")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--book")
    ap.add_argument("--page", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.page:
        r = page_text(a.book, a.page)
        if not r:
            sys.exit(f"[wd408] 没有 p{a.page}（book={a.book}）")
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1)); return
        print(f"# {r['book']} · PDF 第 {r['pdf_page']} 页（原书 p.{r['printed']}）\n")
        print(r["text"]); return

    terms = [t for t in re.split(r"[\s,，、;；]+", " ".join(a.query)) if t]
    if not terms:
        sys.exit(__doc__)
    hits = search(terms, a.book, a.k)
    if a.json:
        print(json.dumps(hits, ensure_ascii=False, indent=1)); return
    if not hits:
        print("[wd408] 无命中 —— 换中文考点词再试（别用公式串，OCR 必错）"); return
    for h in hits:
        print(f"· {h['book']} · PDF 第 {h['pdf_page']} 页（原书 p.{h['printed']}）  score={h['score']}")
        print("  " + snippet(h["text"], terms))
        print()


if __name__ == "__main__":
    main()
