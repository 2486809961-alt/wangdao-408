#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Obsidian JSON Canvas 关系网图（按科目 + 全科总览 + 考点×年份）"""
import json, os, re, collections

OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序")]


def fix_ocr(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t

VAULT = "/Users/jiarun/Documents/王道408"
idx = json.load(open("/tmp/wd_index.json"))
kd = json.load(open("/tmp/wd_kaodian.json"))["kaodian"]

COLOR = {"数据结构": "4", "计算机组成原理": "6", "操作系统": "5", "计算机网络": "3"}
SUBJ_ORDER = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
TOP_PER_CH = 6


PREFIX = {"数据结构": "S", "计算机组成原理": "Z", "操作系统": "O", "计算机网络": "N"}


def card(subj, ch):
    num = int(re.match(r"^第\s*(\d+)\s*章", ch).group(1))
    name = re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")
    return f"{PREFIX[subj]}{num:02d} {subj} 第{num:02d}章 {name}/本章复盘"


def clean(name):
    n = re.sub(r"^[）)】\s]*", "", name)
    n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix_ocr(n.strip())[:28]


chap_kd = collections.defaultdict(list)
for r in kd:
    for ch in r["chapters"]:
        chap_kd[(r["subject"], ch)].append(r)
for k in chap_kd:
    chap_kd[k].sort(key=lambda r: (-len(r["years"]), r["name"]))


class Canvas:
    def __init__(self):
        self.nodes, self.edges, self.n = [], [], 0

    def add(self, x, y, w, h, text, color=None):
        self.n += 1
        node = {"id": f"n{self.n}", "type": "text", "x": x, "y": y,
                "width": w, "height": h, "text": text}
        if color:
            node["color"] = color
        self.nodes.append(node)
        return node["id"]

    def link(self, a, b, color=None, label=None):
        e = {"id": f"e{len(self.edges) + 1}", "fromNode": a, "toNode": b}
        if color:
            e["color"] = color
        if label:
            e["label"] = label
        self.edges.append(e)

    def save(self, name):
        os.makedirs(f"{VAULT}/图谱", exist_ok=True)
        json.dump({"nodes": self.nodes, "edges": self.edges},
                  open(f"{VAULT}/图谱/{name}", "w"), ensure_ascii=False, indent=1)
        print(f"{name}: {len(self.nodes)} 节点 / {len(self.edges)} 边")


def build_tree(cv, subjects, y0=0):
    y = y0
    for subj in subjects:
        chs = [c for c in next(s for s in idx if s["subject"] == subj)["chapters"] if c["secs"]]
        kd_n = sum(len(chap_kd[(subj, c["title"])]) for c in chs)
        sn = cv.add(0, y, 300, 90 + 120 * len(chs),
                    f"## {subj}\n\n{len(chs)} 章 · **{kd_n}** 个考点\n\n[[{subj}·考点总览]]", COLOR[subj])
        cy = y
        for c in chs:
            kds = chap_kd[(subj, c["title"])][:TOP_PER_CH]
            ch_h = 130 + 100 * len(kds)
            cn = cv.add(430, cy, 340, ch_h,
                        f"**{c['title']}**\n\nPDF p{c['page']}–{c['end']}\n原书 p.{c['page']-12}–{c['end']-12}\n\n[[{card(subj, c['title'])}]]",
                        "1")
            cv.link(sn, cn, COLOR[subj])
            ky = cy + 100
            for r in kds:
                kn = cv.add(880, ky, 430, 78,
                            f"{clean(r['name'])}\n`{len(r['years'])} 年 · {'、'.join(r['years'])}`",
                            COLOR[subj])
                cv.link(cn, kn, COLOR[subj])
                ky += 100
            cy += ch_h + 45
        y = cy + 140
    return y


# 1) 四张分科图
for subj in SUBJ_ORDER:
    cv = Canvas()
    build_tree(cv, [subj])
    cv.save(f"知识网·{subj}.canvas")

# 2) 全科总览
cv = Canvas()
build_tree(cv, SUBJ_ORDER)
cv.save("408 知识网·全科.canvas")

# 3) 考点 × 真题年份
zts = [o for o in json.load(open("/tmp/wd_zhenti.json")) if o["kind"] == "zhenti"]
years = sorted({y for r in kd for y in r["years"]})
hot = sorted([r for r in kd if len(r["years"]) >= 3], key=lambda r: -len(r["years"]))[:45]
cv = Canvas()
yn = {}
for i, y in enumerate(years):
    yn[y] = cv.add(0, i * 115, 190, 66, f"**{y}**", "2")
for i, r in enumerate(hot):
    cn = cv.add(620, i * 125, 470, 92,
                f"**{clean(r['name'])}**\n`{r['subject']} · {len(r['years'])} 年考过`\n"
                f"PDF p{r['pages'][0]}（原书 p.{r['pages'][0]-12}）", COLOR[r["subject"]])
    for y in r["years"]:
        if y in yn:
            cv.link(cn, yn[y], COLOR[r["subject"]])
cv.save("真题年份网·考点-年份.canvas")
print("done")
