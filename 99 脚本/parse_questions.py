#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按页流式切题：王道每节「本节习题」+「答案与解析」→ 一道道题（含页码）"""
import sqlite3, re, json

DB = "/Users/jiarun/.dsh/skills/obsidian-exam-recap/index/kb.db"
secs = json.load(open("/tmp/wd_sections.json"))
SUBJ_BOOK = {"数据结构": "27王道《数据结构》高清带书签", "计算机组成原理": "27王道《计算机组成原理》高清带书签",
             "操作系统": "王道2027操作系统-高清带书签", "计算机网络": "27王道《计算机网络》高清带书签"}
con = sqlite3.connect(DB, timeout=60); con.execute("PRAGMA busy_timeout=60000")
_t2i = {t: i for i, t in con.execute("SELECT id,title FROM docs WHERE vault='王道408' AND kind='pdf'")}

HEAD = re.compile(r"^(第\s*\d+\s*章[^\n]{0,14}|20\d{2}年[^\n]{0,24}(指导|复习))\s*$")
FOOT = re.compile(r"^\s*\d{1,4}\s*$")
QNO = re.compile(r"^\s*(\d{1,2})\s*[.、．]\s*")

def page_lines(did, p):
    r = con.execute("SELECT text FROM chunks WHERE doc_id=? AND loc=?", (did, f"p{p}")).fetchone()
    if not r:
        return []
    out = []
    for l in r[0].splitlines():
        s = l.strip()
        if not s or HEAD.match(s) or FOOT.match(s):
            continue
        out.append(s)
    return out

def sec_pages(did, a, b):
    return [(p, page_lines(did, p)) for p in range(a, b + 1)]

def find_blocks(pages):
    """返回 (习题区起始 (p, line_idx), 答案区起始 (p, line_idx))"""
    q = a = None
    for p, lines in pages:
        for i, s in enumerate(lines):
            if q is None:
                m = re.search(r"(本节试题精选|本节习题)", s)
                if m:
                    ctx = s[:m.start()]
                    ok = bool(re.search(r"\d+\.\d+", ctx)) or s.strip().startswith(m.group(1)) or len(ctx.strip()) <= 8
                    if ok:
                        q = (p, i + (0 if s.strip().startswith(m.group(1)) else 1))
                        continue
            if q and a is None and re.search(r"答案与解析", s):
                a = (p, i + 1)
    return q, a

def collect(pages, start, stop):
    """从 start 起收集到 stop（含页码），返回 [(page, line)]"""
    out, on = [], False
    for p, lines in pages:
        for i, s in enumerate(lines):
            if not on:
                if start and p == start[0] and i >= start[1]:
                    on = True
                else:
                    continue
            if stop and p == stop[0] and i >= stop[1]:
                return out
            out.append((p, s))
    return out

def build_items(stream, qtype):
    items, cur = [], None
    for p, s in stream:
        if re.match(r"^(一|二)、\s*(单项选择题|综合应用题)", s):
            continue
        m = QNO.match(s)
        if m:
            if cur:
                items.append(cur)
            cur = {"no": int(m.group(1)), "page": p, "lines": [s[m.end():]]}
        elif cur is not None:
            cur["lines"].append(s)
    if cur:
        items.append(cur)
    for it in items:
        it["text"] = re.sub(r"\n{2,}", "\n", "\n".join(x for x in it["lines"] if x.strip())).strip()
        del it["lines"]
    return items

def split_types(stream):
    """按 一、单项选择题 / 二、综合应用题 切成两段"""
    sel, cmp_, cur = [], [], "sel"
    for p, s in stream:
        if re.match(r"^一、\s*单项选择题", s):
            cur = "sel"; continue
        if re.match(r"^二、\s*综合应用题", s):
            cur = "cmp"; continue
        (sel if cur == "sel" else cmp_).append((p, s))
    return sel, cmp_

out = []
for r in secs:
    did = _t2i[SUBJ_BOOK[r["subject"]]]
    pages = sec_pages(did, r["page"], r["end"])
    q, a = find_blocks(pages)
    if not (q and a):
        continue
    qstream = collect(pages, q, a)
    astream = collect(pages, a, None)
    qsel, qcmp = split_types(qstream)
    asel, acmp = split_types(astream)
    qs = []
    for qtype, qstream_, astream_ in (("选择", qsel, asel), ("综合", qcmp, acmp)):
        ans = {i["no"]: i for i in build_items(astream_, qtype)}
        for it in build_items(qstream_, qtype):
            if len(it["text"]) < 12:
                continue
            a_ = ans.get(it["no"])
            ans_txt = a_["text"] if a_ else ""
            if qtype == "选择" and ans_txt:
                m = re.match(r"^([A-D])\b\s*(.*)$", ans_txt, re.S)
                if m:
                    ans_txt = m.group(1) + "\n" + m.group(2).strip()
            qs.append({"qtype": qtype, "no": it["no"], "stem": it["text"], "page": it["page"],
                       "answer": ans_txt, "answer_page": a_["page"] if a_ else None})
    out.append({"subject": r["subject"], "chapter": r["chapter"], "sec": r["sec"],
                "questions": qs})

json.dump(out, open("/tmp/wd_questions.json", "w"), ensure_ascii=False)
tot = sum(len(s["questions"]) for s in out)
sel_n = sum(1 for s in out for q in s["questions"] if q["qtype"] == "选择")
ans_n = sum(1 for s in out for q in s["questions"] if q["answer"])
print(f"节 {len(out)} · 题 {tot}（选择 {sel_n} / 综合 {tot-sel_n}）· 有答案 {ans_n}")
s72 = [s for s in out if "7.2 顺序查找" in s["sec"]]
if s72:
    for q in s72[0]["questions"][:2]:
        print("---", q["qtype"], q["no"], "p", q["page"], "ans_p", q["answer_page"])
        print("Q:", q["stem"][:90].replace("\n", " / "))
        print("A:", q["answer"][:90].replace("\n", " / "))
