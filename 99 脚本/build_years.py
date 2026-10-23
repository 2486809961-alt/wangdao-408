#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每一年一篇真题清单：题目 → 同页考点 → 教材页 → 同类年份"""
import json, os, re, collections

OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序")]


def fix_ocr(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t

VAULT = "/Users/jiarun/Documents/王道408"
raw = json.load(open("/tmp/wd_zhenti.json"))
zts = [o for o in raw if o["kind"] == "zhenti"]
tr = [o for o in raw if o["kind"] == "track"]

def clean(n):
    n = re.sub(r"^[）)】\s]*", "", n)
    n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix_ocr(n.strip())[:34]

PREFIX = {"数据结构": "S", "计算机组成原理": "Z", "操作系统": "O", "计算机网络": "N"}


def card(subj, ch):
    num = int(re.match(r"^第\s*(\d+)\s*章", ch).group(1))
    name = re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")
    return f"{PREFIX[subj]}{num:02d} {subj} 第{num:02d}章 {name}/本章复盘"

# 同章同页附近（±4 页）的考点
near = collections.defaultdict(list)
for t in tr:
    near[(t["subject"], t["chapter"], t["pdf_page"])].append(t)
def linked(subj, ch, pg):
    out = {}
    for d in range(0, 5):
        for p in (pg - d, pg + d):
            for t in near.get((subj, ch, p), []):
                out[(t["name"], tuple(t["years"]))] = t["years"]
    return [{"name": k[0], "years": v} for k, v in out.items()]

by_year = collections.defaultdict(list)
for o in zts:
    by_year[o["year"]].append(o)

os.makedirs(f"{VAULT}/真题", exist_ok=True)
for y, items in by_year.items():
    items.sort(key=lambda o: (o["subject"], o["pdf_page"]))
    L = ["---", "type: zhenti", f"year: {y}", "tags: [408, 真题]", "---", "",
         f"# {y} 年 408 真题清单", "",
         f"> 来源：王道四本书内的真题原文/引用，共 **{len(items)} 条**。页码是王道书内位置（PDF p / 原书 p）。",
         f"> 返回：[[408 历年真题索引]] · 图谱：[[真题年份网·考点-年份]]", ""]
    cur = None
    for o in items:
        if o["subject"] != cur:
            cur = o["subject"]
            L += [f"## {cur}", ""]
        stem = re.sub(r"\s+", " ", o["stem"]).strip()
        stem = re.split(r"【\s*20\d{2}", stem)[0]
        stem = re.split(r"答案与解析|【解答】", stem)[0]
        stem = re.sub(r"\s*\d+\.\s*(19|20)\d{2}.*$", "", stem).strip()[:110]
        L += [f"- [ ] **题干**：" + stem,
              f"  - 位置：[[{card(o['subject'], o['chapter'])}]] · PDF p{o['pdf_page']}（原书 p.{o['pdf_page']-12}）"]
        lk = linked(o["subject"], o["chapter"], o["pdf_page"])
        if lk:
            L.append("  - 同页考点（自动关联）：" +
                     "；".join(f"{clean(k['name'])}（{'、'.join(k['years'])}）" for k in lk[:3]))
        L.append("")
    open(f"{VAULT}/真题/{y} 真题清单.md", "w").write("\n".join(L))
print("写入年份清单:", len(by_year))
