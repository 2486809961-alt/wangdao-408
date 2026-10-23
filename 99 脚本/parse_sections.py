#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「节」切分王道每节习题与答案解析，供后续装配 1000 题结构"""
import sqlite3, re, json, os

DB = "/Users/jiarun/.dsh/skills/obsidian-exam-recap/index/kb.db"
idx = json.load(open("/tmp/wd_index.json"))
SUBJ_BOOK = {"数据结构": "27王道《数据结构》高清带书签", "计算机组成原理": "27王道《计算机组成原理》高清带书签",
             "操作系统": "王道2027操作系统-高清带书签", "计算机网络": "27王道《计算机网络》高清带书签"}

con = sqlite3.connect(DB, timeout=60); con.execute("PRAGMA busy_timeout=60000")

def pages_of(title):
    did = con.execute("SELECT id FROM docs WHERE title=? AND vault='王道408'", (title,)).fetchone()[0]
    out = {}
    for loc, text in con.execute("SELECT loc,text FROM chunks WHERE doc_id=? ORDER BY CAST(SUBSTR(loc,2) AS INTEGER)", (did,)):
        out[int(loc[1:])] = text
    return out

result = []
for s in idx:
    subj = s["subject"]
    pages = pages_of(SUBJ_BOOK[subj])
    for c in s["chapters"]:
        if not c["secs"]:
            continue
        secs = c["secs"]
        # 每节：[page, end]
        for i, sec in enumerate(secs):
            end = secs[i + 1]["page"] - 1 if i + 1 < len(secs) else c["end"]
            if re.search(r"归纳总结|思维拓展|疑难点|本章小结|考纲|复习提示", sec["title"]):
                continue
            text = {}
            for p in range(sec["page"], end + 1):
                if p in pages:
                    text[p] = pages[p]
            if not text:
                continue
            # 找「本节试题精选 / 习题」页
            q_start = None; a_start = None
            for p in sorted(text):
                flat = re.sub(r"\s+", "", text[p])
                if q_start is None and re.search(r"(本节试题精选|本节习题|^习题|【习题】)", flat):
                    q_start = p
                if q_start and a_start is None and p >= q_start and "答案与解析" in flat:
                    a_start = p
            result.append({"subject": subj, "chapter": c["title"], "sec": sec["title"],
                           "page": sec["page"], "end": end,
                           "q_start": q_start, "a_start": a_start,
                           "has_pages": len(text)})
json.dump(result, open("/tmp/wd_sections.json", "w"), ensure_ascii=False)
ok = [r for r in result if r["q_start"] and r["a_start"]]
print(f"节 {len(result)} 个，其中找到习题+答案 {len(ok)} 个")
nd = [r for r in result if not (r["q_start"] and r["a_start"])]
print("未定位:", [(r["subject"][:2], r["sec"], r["page"], r["q_start"], r["a_start"]) for r in nd][:10])
for r in [x for x in ok if x["subject"] == "数据结构"][:8]:
    print(" ", r["sec"], "习题 p", r["q_start"], "答案 p", r["a_start"], "节尾", r["end"])
