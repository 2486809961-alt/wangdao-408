#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大类（板块）页 + 大类总览 + 大类网 canvas"""
import json, os, re, collections
from blocks import BLOCKS

VAULT = "/Users/jiarun/Documents/王道408"
OFF = 12
PREFIX = {"数据结构": "S", "计算机组成原理": "Z", "操作系统": "O", "计算机网络": "N"}
COLOR = {"数据结构": "4", "计算机组成原理": "6", "操作系统": "5", "计算机网络": "3"}
data = json.load(open("/tmp/wd_questions.json"))
idx = json.load(open("/tmp/wd_index.json"))
kds = json.load(open("/tmp/wd_kaodian.json"))["kaodian"]
tracks = [o for o in json.load(open("/tmp/wd_zhenti.json")) if o["kind"] == "track"]
OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序"),
           ("顺宇表", "顺序表"), ("有厚", "有序")]
def fix(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t
def chnum(ch): return int(re.match(r"^第\s*(\d+)\s*章", ch).group(1))
def chname(ch): return re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")
def folder(subj, ch): return f"{PREFIX[subj]}{chnum(ch):02d} {subj} 第{chnum(ch):02d}章 {chname(ch)}"
def clean_kd(n):
    n = re.sub(r"^[）)】\s]*", "", n); n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix(n.strip())[:34].replace("/", "／")

qcount = collections.Counter((s["subject"], s["chapter"]) for s in data for q in s["questions"])
CH = {(s["subject"], c["title"]): c for s in idx for c in s["chapters"]}

os.makedirs(f"{VAULT}/ZZ 大类", exist_ok=True)
rows_all = []
for subj, blocks in BLOCKS.items():
    for name, chs, desc in blocks:
        chaps = [(s_, c_) for (s_, c_) in CH if s_ == subj and chnum(c_) in chs]
        chaps.sort(key=lambda t: chnum(t[1]))
        nq = sum(qcount[(s, c)] for s, c in chaps)
        yrs = collections.Counter()
        kd_set = []
        for s, c in chaps:
            for t in tracks:
                if t["subject"] == s and t["chapter"] == c:
                    for y in t["years"]:
                        yrs[y] += 1
            for k in kds:
                if k["subject"] == s and c in k["chapters"]:
                    kd_set.append(k)
        kd_uniq, seen = [], set()
        for k in sorted(kd_set, key=lambda k: -len(k["years"])):
            nm = clean_kd(k["name"])
            if nm in seen:
                continue
            seen.add(nm); kd_uniq.append((nm, k))
        L = ["---", "type: block", f"subject: {subj}", f'block: "{name}"',
             f"chapters: {len(chaps)}", f"questions: {nq}",
             f"tags: [408, {subj}, 大类]", "---", "",
             f"# 大类：{name}", "",
             f"> {subj} · {desc}。",
             f"> 含 **{len(chaps)} 章 / {nq} 题**；王道标注过真题的年份 {len(yrs)} 个。",
             f"> 图谱：[[408 大类网]] · 返回：[[大类总览]] · [[408 MOC]]", "",
             "## 章节", "", "| 章 | 题数 | 页码范围（PDF / 原书） |", "| --- | --- | --- |"]
        for s, c in chaps:
            ci = CH[(s, c)]
            L.append(f"| [[{folder(s, c)}/本章复盘\\|{c}]] | {qcount[(s,c)]} | "
                     f"{ci['page']}–{ci['end']} / p.{ci['page']-OFF}–{ci['end']-OFF} |")
        L += ["", f"## 高频考点（{len(kd_uniq)}）", ""]
        for nm, k in kd_uniq[:16]:
            L.append(f"- [[ZZ 考点/{nm}|{nm}]]（{'、'.join(k['years'])}）")
        if len(kd_uniq) > 16:
            L.append(f"- …… 其余 {len(kd_uniq)-16} 个见 [[考点总索引]]")
        L += ["", "## 真题年份", ""]
        if yrs:
            L.append("、".join(f"{y}（{c} 次）" for y, c in sorted(yrs.items())))
            L += ["", "按年清单：" + " · ".join(f"[[{y} 真题清单]]" for y in sorted(yrs))]
        else:
            L.append("（王道未标注）")
        L.append("")
        nf = name.replace("/", "／")
        open(f"{VAULT}/ZZ 大类/{subj} · {nf}.md", "w").write("\n".join(L) + "\n")
        rows_all.append((subj, name, len(chaps), nq, len(yrs), sorted(yrs)))

# 大类总览
L = ["---", "type: index", "tags: [408, 大类]", "---", "", "# 408 大类总览", "",
     "> 26 章 → **15 个大板块**。先按大板块建立框架，再往里装章节和题目。", "",
     "| 科目 | 大类 | 章数 | 题数 | 真题年份数 |", "| --- | --- | --- | --- | --- |"]
for subj, name, nc, nq, ny, _ in rows_all:
    L.append(f"| {subj} | [[ZZ 大类/{subj} · {name.replace('/', '／')}\\|{name}]] | {nc} | {nq} | {ny} |")
tot = sum(r[3] for r in rows_all)
L += ["", f"合计 **{tot}** 题 / 15 大类 / 26 章。", "",
      "图谱：[[408 大类网]]（科目 → 大类 → 章）· [[408 知识网·全科]]（章 → 考点）· [[真题年份网·考点-年份]]", ""]
open(f"{VAULT}/00 索引/大类总览.md", "w").write("\n".join(L) + "\n")
print("大类页:", len(rows_all), "题:", tot)

# 大类网 canvas
nodes, edges, nid = [], [], [0]
def add(x, y, w, h, text, color=None):
    nid[0] += 1
    n = {"id": f"n{nid[0]}", "type": "text", "x": x, "y": y, "width": w, "height": h, "text": text}
    if color: n["color"] = color
    nodes.append(n)
    return n["id"]
def link(a, b, color=None):
    edges.append({"id": f"e{len(edges)+1}", "fromNode": a, "toNode": b, **({"color": color} if color else {})})

y = 0
for subj in ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]:
    blocks = [r for r in rows_all if r[0] == subj]
    nq = sum(r[3] for r in blocks)
    sn = add(0, y, 300, 100 + 150 * len(blocks),
             f"# {subj}\n\n{len(blocks)} 大类 · {sum(r[2] for r in blocks)} 章 · {nq} 题",
             COLOR[subj])
    by = y
    for subj_, name, nc, nqq, ny, yrs in blocks:
        bh = 100 + 110 * nc
        bn = add(430, by, 380, bh,
                 f"## {name}\n`{nc} 章 · {nqq} 题 · {ny} 年考过`\n\n{('、'.join(yrs)) if yrs else ''}",
                 COLOR[subj])
        link(sn, bn, COLOR[subj])
        ky = by + 95
        ch_nums = next(b[1] for b in BLOCKS[subj] if b[0] == name)
        for c in sorted([c for (s_, c) in CH if s_ == subj and chnum(c) in ch_nums], key=chnum):
            cn = add(900, ky, 420, 82,
                     f"**{c}**\n`{qcount[(subj, c)]} 题`\n[[{folder(subj, c)}/本章复盘|本章复盘]]", "1")
            link(bn, cn, COLOR[subj])
            ky += 110
        by += bh + 40
    y = by + 90

json.dump({"nodes": nodes, "edges": edges},
          open(f"{VAULT}/图谱/408 大类网.canvas", "w"), ensure_ascii=False, indent=1)
print(f"408 大类网.canvas: {len(nodes)} 节点 / {len(edges)} 边")
