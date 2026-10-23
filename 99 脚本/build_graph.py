#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""王道 408：真题 × 考点 → 章卡补真题分布 + 真题索引 + 关系网 Canvas"""
import json, os, re, collections

VAULT = "/Users/jiarun/Documents/王道408"
OFF = 12
SUBJ_COLOR = {"数据结构": "4", "计算机组成原理": "6", "操作系统": "5", "计算机网络": "3"}
data = json.load(open("/tmp/wd_zhenti.json"))
idx = json.load(open("/tmp/wd_index.json"))

tracks = [o for o in data if o["kind"] == "track"]
zts = [o for o in data if o["kind"] == "zhenti"]

# ---- 考点聚合（同名合并，保留科目/章/页码/年份）
K = {}
for o in tracks:
    name = re.sub(r"^.*?[）)]", "", o["name"]).strip() or o["name"]
    key = (o["subject"], name)
    r = K.setdefault(key, {"subject": o["subject"], "name": name, "chapters": set(),
                           "pages": set(), "years": set()})
    r["chapters"].add(o["chapter"]); r["pages"].add(o["pdf_page"]); r["years"].update(o["years"])

# ---- 真题聚合（按 年份+科目+章 去重题干）
Z = {}
for o in zts:
    stem = re.sub(r"\s+", "", o["stem"])[:16]
    key = (o["year"], o["subject"], o["chapter"], stem)
    if key not in Z or o["pdf_page"] < Z[key]["pdf_page"]:
        Z[key] = o

# ---- 章 → 考点（按年份数排序）
chap_kd = collections.defaultdict(list)
for r in K.values():
    for ch in r["chapters"]:
        chap_kd[(r["subject"], ch)].append(r)
for k in chap_kd:
    chap_kd[k].sort(key=lambda r: (-len(r["years"]), r["name"]))

# ---- 章 → 真题
chap_zt = collections.defaultdict(list)
for o in Z.values():
    chap_zt[(o["subject"], o["chapter"])].append(o)
for k in chap_zt:
    chap_zt[k].sort(key=lambda o: (o["year"], o["pdf_page"]))

kaodian_total = len(K)
zhenti_total = len(Z)
year_all = sorted({o["year"] for o in Z.values()})

json.dump({"kaodian": [dict(r, chapters=sorted(r["chapters"]), pages=sorted(r["pages"]),
                           years=sorted(r["years"])) for r in K.values()]},
          open("/tmp/wd_kaodian.json", "w"), ensure_ascii=False)
print(f"考点 {kaodian_total} 个 · 真题条目 {zhenti_total} 条 · 年份 {year_all[0]}–{year_all[-1]}")
print("高频考点 top10:", [(r["name"], len(r["years"])) for r in
                         sorted(K.values(), key=lambda r: -len(r["years"]))[:10]])
