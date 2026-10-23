#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""00 索引：README / 408 MOC / 章节与考点对照 / 考点总索引"""
import json, os, re, collections

VAULT = "/Users/jiarun/Documents/王道408"
OFF = 12
PREFIX = {"数据结构": "S", "计算机组成原理": "Z", "操作系统": "O", "计算机网络": "N"}
data = json.load(open("/tmp/wd_questions.json"))
idx = json.load(open("/tmp/wd_index.json"))
kds = json.load(open("/tmp/wd_kaodian.json"))["kaodian"]
OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序"),
           ("顺宇表", "顺序表"), ("有厚", "有序")]
def fix(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t
def chnum(ch): return int(re.match(r"^第\s*(\d+)\s*章", ch).group(1))
def chname(ch): return re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")
def folder(subj, ch): return f"{PREFIX[subj]}{chnum(ch):02d} {subj} 第{chnum(ch):02d}章 {chname(ch)}"
def clean_kd(name):
    n = re.sub(r"^[）)】\s]*", "", name); n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix(n.strip())[:34].replace("/", "／")

# 统计
per_chap = collections.Counter((s["subject"], s["chapter"]) for s in data for q in s["questions"])
kd_all = collections.OrderedDict()
for k in kds:
    nm = clean_kd(k["name"])
    r = kd_all.setdefault(nm, {"subj": set(), "chy": set(), "y": set()})
    r["subj"].add(k["subject"]); r["chy"].update(k["chapters"]); r["y"].update(k["years"])

os.makedirs(f"{VAULT}/00 索引", exist_ok=True)

# 1) README
tot = sum(per_chap.values())
L = ["---", "type: index", "tags: [408, README]", "---", "",
     "# 王道 408 · 题库（1000 题结构）", "",
     f"> {tot} 道题，一题一篇；{len(per_chap)} 章，一章一目录；{len(kd_all)} 个考点各一页。",
     "> 全部来自《王道 2027 数据结构 / 计算机组成原理 / 操作系统 / 计算机网络》(扫描版 OCR)。", "",
     "## 目录约定（与「张宇1000题」库同构）", "",
     "```",
     "王道408/",
     "  S01 数据结构 第01章 绪论/     ← 一章一目录",
     "      本章复盘.md               ← 小节页码 + 题目清单 + 真题分布",
     "      题目/第1章 第01题.md      ← 一题一篇（题干/答案/解析/考点/出处）",
     "  ZZ 考点/<考点名>.md           ← 考点页，反向挂回所有题目",
     "  ZZ 错题复盘/                  ← 我自己的复盘（note.py 产出）",
     "  真题/<年份> 真题清单.md       ← 历年真题索引",
     "  图谱/*.canvas                 ← 关系网图",
     "  00 索引/                      ← 本目录",
     "```", "",
     "## 三条命令", "",
     "```bash",
     'cd "/Users/jiarun/Documents/王道408"',
     'S=/Users/jiarun/.dsh/skills/obsidian-exam-recap/scripts',
     'python3 "99 脚本/wd408.py" "快表 有效访问时间" --book os -k 5   # 查考点→双页码',
     'python3 $S/kb.py find "分块查找" -k 6 --vault 王道408            # 全库检索',
     'python3 $S/note.py /tmp/recap.json --open                        # 复盘落盘(自动 1000 题版式)',
     "```", "",
     "## 索引页", "",
     "- [[大类总览]] · 科目 → **大类** → 章 → 题数",
     "- [[408 MOC]] · 科目 → 章 → 题数（明细）",
     "- [[章节与知识点对照]] · 章 ↔ 考点",
     "- [[考点总索引]] · 全部考点",
     "- [[408 历年真题索引]] · 2009–2025",
     "- [[考点×年份 热力表]] · 高频考点矩阵",
     "- [[图谱说明]] · 6 张关系网图",
     "",
     "## 读法", "",
     "0. 先看 [[大类总览]] / [[408 大类网]]，按大板块建框架（15 个大类）。",
     "1. 再看 `本章复盘` 的题目清单，按题号顺序刷，刷一题开一题。",
     "2. 卡住 → 看该题 `[!info] 本节考点` 里的 2–3 个考点页 → 考点页里挂着的同考点题一起过。",
     "3. 错题 → `ZZ 错题复盘/`，用 [[单题复盘模板]] 五步走完。",
     ""]
open(f"{VAULT}/00 索引/README.md", "w").write("\n".join(L) + "\n")

# 2) 408 MOC
L = ["---", "type: moc", "tags: [408, MOC]", "---", "", "# 408 MOC", "",
     "| 科目 | 大类 | 章 | 题数 | 目录 |", "| --- | --- | --- | --- | --- |"]
import sys; sys.path.insert(0, ".")
from blocks import block_of
for (subj, ch), n in sorted(per_chap.items(), key=lambda kv: (PREFIX[kv[0][0]], chnum(kv[0][1]))):
    blk, _ = block_of(subj, chnum(ch))
    L.append(f"| {subj} | [[ZZ 大类/{subj} · {blk.replace('/', '／')}\\|{blk}]] | 第{chnum(ch)}章 {chname(ch)} | {n} | [[{folder(subj, ch)}/本章复盘\\|本章复盘]] |")
L += ["", f"合计 **{tot}** 题。", "",
      "| 科目 | 题目 | 考点 | 真题 |", "| --- | --- | --- | --- |"]
for subj in PREFIX:
    n = sum(v for (s, _), v in per_chap.items() if s == subj)
    L.append(f"| {subj} | {n} | {len([1 for r in kd_all.values() if subj in r['subj']])} | 见 [[408 历年真题索引]] |")
open(f"{VAULT}/00 索引/408 MOC.md", "w").write("\n".join(L) + "\n")

# 3) 章节与知识点对照
L = ["---", "type: index", "tags: [408, 对照]", "---", "", "# 章节与知识点对照", "",
     "> 每章：小节页码 + 该章考点（王道标注年份）+ 题数。", ""]
for s in idx:
    subj = s["subject"]
    L += [f"## {subj}", ""]
    for c in [c for c in s["chapters"] if c["secs"]]:
        n = per_chap.get((subj, c["title"]), 0)
        L.append(f"### [[{folder(subj, c['title'])}/本章复盘|第{chnum(c['title'])}章 {chname(c['title'])}]] · {n} 题")
        L.append("")
        L.append("| 小节 | PDF 页 | 原书页 |")
        L.append("| --- | --- | --- |")
        for sec in c["secs"]:
            L.append(f"| {sec['title']} | {sec['page']}–{sec['end']} | {sec['page']-OFF}–{sec['end']-OFF} |")
        ks = [k for k in kds if k["subject"] == subj and c["title"] in k["chapters"]]
        if ks:
            L += ["", "考点：" + " · ".join(f"[[ZZ 考点/{clean_kd(k['name'])}|{clean_kd(k['name'])}]]（{'、'.join(k['years'])}）" for k in ks[:12])]
        L.append("")
open(f"{VAULT}/00 索引/章节与知识点对照.md", "w").write("\n".join(L) + "\n")

# 4) 考点总索引
L = ["---", "type: index", "tags: [408, 考点]", "---", "", "# 考点总索引", "",
     f"> 共 **{len(kd_all)}** 个考点（王道「考点追踪」标注名）。按科目分组，括号内为标注的真题年份。", ""]
for subj in PREFIX:
    L += [f"## {subj}", ""]
    items = [(nm, r) for nm, r in kd_all.items() if subj in r["subj"]]
    items.sort(key=lambda t: (-len(t[1]["y"]), t[0]))
    for nm, r in items:
        L.append(f"- [[ZZ 考点/{nm}|{nm}]]（{'、'.join(sorted(r['y'])) or '无'}）")
    L.append("")
open(f"{VAULT}/00 索引/考点总索引.md", "w").write("\n".join(L) + "\n")
print("索引写完", tot, len(kd_all))
