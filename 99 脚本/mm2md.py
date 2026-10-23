#!/usr/bin/env python3
"""思维导图 PDF -> Obsidian Markdown

导图是自左向右的树：同层节点 x 基本一致，孩子比父亲更靠右。
按 x0 聚类成「层」，行内按 y 排序 → 缩进即层级。
"""
import sys, os, re
import pymupdf

GAP = 45.0


def cluster_x(xs, gap=GAP):
    xs = sorted(set(xs))
    centers, cur = [], [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] <= gap:
            cur.append(x)
        else:
            centers.append(sum(cur) / len(cur))
            cur = [x]
    centers.append(sum(cur) / len(cur))
    return centers


def collect(page):
    items = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            txt = "".join(s["text"] for s in l["spans"]).strip()
            txt = re.sub(r"[\ue000-\uf8ff]", "", txt).strip()
            if not txt:
                continue
            items.append((round(l["bbox"][1], 1), round(l["bbox"][0], 1),
                          round(max(s["size"] for s in l["spans"]), 1), txt))
    return items


def convert(src, dst, title):
    doc = pymupdf.open(src)
    body = []
    for pno in range(doc.page_count):
        items = collect(doc[pno])
        if not items:
            continue
        centers = cluster_x([i[1] for i in items])
        body.append("\n### 第 %d 页\n" % (pno + 1))
        for y, x, size, txt in sorted(items, key=lambda t: (t[0], t[1])):
            lvl = min(range(len(centers)), key=lambda i: abs(centers[i] - x))
            body.append("  " * lvl + "- " + txt)
    lines = ["# " + title + "\n",
             "> 来源 `%s` · 文字层结构化（x 聚类还原层级，%d 页）\n" % (os.path.basename(src), doc.page_count),
             "> 缩进 = 大纲层级；同页多条分支按纵向阅读顺序排列。\n"]
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w").write("\n".join(lines + body) + "\n")
    print("wrote", dst, len(body), "lines")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
