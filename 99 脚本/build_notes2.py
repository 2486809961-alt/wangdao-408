#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, collections

OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序")]


def fix_ocr(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t

VAULT = "/Users/jiarun/Documents/王道408"
idx = json.load(open("/tmp/wd_index.json"))
kd = json.load(open("/tmp/wd_kaodian.json"))["kaodian"]
zts = [o for o in json.load(open("/tmp/wd_zhenti.json")) if o["kind"] == "zhenti"]

def clean(name):
    n = re.sub(r"^[）)】\s]*", "", name)
    n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix_ocr(n.strip())[:34]

def card(subj, ch):
    num = re.match(r"^第\s*(\d+)\s*章", ch).group(1)
    name = re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")
    return f"{subj}/第{num}章 {name}"

chap_kd = collections.defaultdict(list)
for r in kd:
    for ch in r["chapters"]:
        chap_kd[(r["subject"], ch)].append(r)
for k in chap_kd:
    chap_kd[k].sort(key=lambda r: (-len(r["years"]), r["name"]))

chap_zt = collections.defaultdict(list)
for o in zts:
    chap_zt[(o["subject"], o["chapter"])].append(o)
for k in chap_zt:
    chap_zt[k].sort(key=lambda o: (o["year"], o["pdf_page"]))

# ---------- 1. 章卡补「历年真题分布」
START, END = "<!-- ZHENTI-START -->", "<!-- ZHENTI-END -->"
n_done = 0
for s in idx:
    subj = s["subject"]
    for c in [c for c in s["chapters"] if c["secs"]]:
        path = f"{VAULT}/考点/{card(subj, c['title'])}.md"
        if not os.path.exists(path):
            continue
        body = open(path).read()
        body = re.sub(re.escape(START) + r".*?" + re.escape(END), "", body, flags=re.S)
        kds = chap_kd[(subj, c["title"])]
        zt = chap_zt[(subj, c["title"])]
        L = [START, "", "## 历年真题分布（王道标注）", ""]
        if kds:
            L += [f"> 本章共 {len(kds)} 个考点被王道标出真题年份，覆盖 "
                  f"{len({y for r in kds for y in r['years']})} 个年份。", "",
                  "| 考点 | 真题年份 | 年数 |", "| --- | --- | --- |"]
            for r in kds:
                L.append(f"| {clean(r['name'])} | {'、'.join(r['years'])} | {len(r['years'])} |")
            L.append("")
        if zt:
            L += ["### 本章真题条目", "", "| 年份 | 题干（截断） | 教材页 |", "| --- | --- | --- |"]
            for o in zt:
                stem = re.sub(r"\s+", " ", o["stem"])
                stem = re.split(r"【\s*20\d{2}", stem)[0]
                stem = re.split(r"答案与解析|【解答】", stem)[0]
                stem = re.sub(r"\s*\d+\.\s*$", "", stem).strip()[:70]
                L.append(f"| {o['year']} | {stem} | PDF p{o['pdf_page']}（原书 p.{o['pdf_page']-12}） |")
            L.append("")
        L.append("图谱：[[408 知识网·全科]] · [[真题年份网·考点-年份]]")
        L.append("")
        L.append(END)
        body = body.rstrip() + "\n\n" + "\n".join(L) + "\n"
        open(path, "w").write(body)
        n_done += 1
print("章卡已补真题分布:", n_done)

# ---------- 2. 真题索引（按年）
os.makedirs(f"{VAULT}/真题", exist_ok=True)
by_year = collections.defaultdict(list)
for o in zts:
    by_year[o["year"]].append(o)
years = sorted(by_year)
L = ["---", "type: index", "tags: [408, 真题, 索引]", "---", "",
     "# 408 历年真题索引（2009–2025）", "",
     f"> 数据来源：王道四本书内的 **{len(zts)} 条真题标记**（每本书「考点追踪」与习题原文），页码为王道书内位置，非原卷编号。",
     "> 用途：先按年扫一遍知道「这一年考了什么」，再跳回对应章卡的考点表看重复规律。", "",
     "图谱：[[真题年份网·考点-年份]] · [[408 知识网·全科]]", "",
     "| 年份 | 条目数 | 科目分布 |", "| --- | --- | --- |"]
for y in years:
    cnt = collections.Counter(o["subject"] for o in by_year[y])
    L.append(f"| [[{y} 真题清单]] | {len(by_year[y])} | " +
             "、".join(f"{k} {v}" for k, v in cnt.most_common()) + " |")
L.append("")
for y in years:
    L += [f"## {y}", "", "| 科目 | 章 | 题干（截断） | 教材页 |", "| --- | --- | --- | --- |"]
    for o in sorted(by_year[y], key=lambda o: (o["subject"], o["pdf_page"])):
        stem = re.sub(r"\s+", " ", o["stem"])
        stem = re.split(r"【\s*20\d{2}", stem)[0]
        stem = re.split(r"答案与解析|【解答】", stem)[0]
        stem = re.sub(r"\s*\d+\.\s*$", "", stem).strip()[:80]
        L.append(f"| {o['subject']} | [[{card(o['subject'], o['chapter'])}]] | {stem} | p{o['pdf_page']}（原书 p.{o['pdf_page']-12}） |")
    L.append("")
open(f"{VAULT}/真题/408 历年真题索引.md", "w").write("\n".join(L))

# ---------- 3. 考点 × 年份 热力表
top = sorted(kd, key=lambda r: -len(r["years"]))[:80]
L = ["---", "type: index", "tags: [408, 高频考点]", "---", "",
     "# 考点 × 年份 热力表（Top 80）", "",
     f"> 632 个考点里被王道标注 ≥3 个年份的共 **{len([r for r in kd if len(r['years'])>=3])} 个**；下表取年份最多的 80 个。",
     "> `●` = 该年考过。空列代表「近 17 年未单独出题」或「王道未标注」。", "",
     "| 考点 | 科目 | " + " | ".join(y[2:] for y in years) + " | 年数 |",
     "| --- | --- | " + " | ".join("---" for _ in years) + " | --- |"]
for r in top:
    cells = " | ".join("●" if y in r["years"] else "" for y in years)
    L.append(f"| {clean(r['name'])} | {r['subject'][:2]} | {cells} | {len(r['years'])} |")
L += ["", "图谱：[[真题年份网·考点-年份]]", ""]
open(f"{VAULT}/真题/考点×年份 热力表.md", "w").write("\n".join(L))
print("真题索引 + 热力表 已写")
