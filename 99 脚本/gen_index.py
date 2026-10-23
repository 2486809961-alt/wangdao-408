#!/usr/bin/env python3
"""王道 408 教材书签 -> Obsidian 章节索引笔记"""
import os, re, sys, json
import pymupdf

VAULT = "/Users/jiarun/Documents/王道408"
OFFSET = 12  # 印刷页码 = PDF 页码 - 12（四本已核对：PDF p60 = 原书 p48）

BOOKS = [
    ("数据结构", "00 教材/27王道《数据结构》高清带书签.pdf", "27王道《数据结构》"),
    ("计算机组成原理", "00 教材/27王道《计算机组成原理》高清带书签.pdf", "27王道《计算机组成原理》"),
    ("操作系统", "00 教材/王道2027操作系统-高清带书签.pdf", "王道2027操作系统"),
    ("计算机网络", "00 教材/27王道《计算机网络》高清带书签.pdf", "27王道《计算机网络》"),
]

SKIP = {"前   言", "前 言", "致  读  者", "王道训练营", "目   录", "参 考 文 献", "参考文献"}


def clean(t):
    t = re.sub(r"\s+", " ", t).strip()
    return t


def pdfpage_to_int(p):
    return int(p) if str(p).isdigit() else None


def main():
    subjects = []
    for subj, rel, short in BOOKS:
        doc = pymupdf.open(os.path.join(VAULT, rel))
        toc = doc.get_toc()
        chapters = []
        cur = None
        for lvl, title, page in toc:
            t = clean(title)
            if t in SKIP or re.match(r"^[\d\s\W]*$", t):
                continue
            if lvl == 1 and re.match(r"^第\s*\d+\s*章", t):
                cur = {"title": t, "page": page, "secs": []}
                chapters.append(cur)
            elif lvl == 2 and cur is not None:
                cur["secs"].append({"title": t, "page": page})
        # 章节页范围
        for i, c in enumerate(chapters):
            nxt = None
            for j in range(i + 1, len(chapters)):
                nxt = chapters[j]["page"]
                break
            c["end"] = (nxt - 1) if nxt else doc.page_count - 1
            for s, ns in zip(c["secs"], c["secs"][1:] + [{"page": c["end"] + 1}]):
                s["end"] = ns["page"] - 1
            if c["secs"]:
                c["secs"][-1]["end"] = c["end"]
            if c["secs"]:
                c["secs"][0]["page"] = c["secs"][0]["page"]
        subjects.append({"subject": subj, "book": rel, "short": short,
                         "pages": doc.page_count, "chapters": chapters})
        print(subj, doc.page_count, "p /", len(chapters), "章")

    json.dump(subjects, open("/tmp/wd_index.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
