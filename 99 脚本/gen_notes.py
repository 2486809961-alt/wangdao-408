#!/usr/bin/env python3
import json, os, re

VAULT = "/Users/jiarun/Documents/王道408"
OFF = 12
data = json.load(open("/tmp/wd_index.json"))

MM = {"数据结构": "数据结构·思维导图", "计算机组成原理": "计算机组成原理·思维导图",
      "操作系统": "操作系统·思维导图", "计算机网络": "计算机网络·思维导图"}

def printed(p):
    return p - OFF

subject_lines = []
for s in data:
    subj = s["subject"]
    chs = [c for c in s["chapters"] if c["secs"]]
    os.makedirs(f"{VAULT}/考点/{subj}", exist_ok=True)
    for c in chs:
        num = re.match(r"^第\s*(\d+)\s*章", c["title"]).group(1)
        body = []
        body.append("---")
        body.append("type: kaodian")
        body.append(f"subject: {subj}")
        body.append(f"chapter: {num}")
        body.append('chapter_name: "%s"' % re.sub(r"^第\s*\d+\s*章\s*", "", c["title"]))
        body.append(f'book: "{s["short"]}"')
        body.append(f"pdf_pages: {c['page']}-{c['end']}")
        body.append(f"printed_pages: {printed(c['page'])}-{printed(c['end'])}")
        body.append(f"tags: [408, {subj}, 考点]")
        body.append("---")
        body.append("")
        body.append(f"# {c['title']}")
        body.append("")
        body.append("> [!info] 教材位置")
        body.append(f"> `{s['book']}` · **PDF 第 {c['page']}–{c['end']} 页**（原书 p.{printed(c['page'])}–{printed(c['end'])}）")
        body.append("")
        body.append(f"返回：[[{subj}·考点总览]] · 图解：[[{MM[subj]}]]")
        body.append("")
        body.append("## 小节与页码")
        body.append("")
        body.append("| 小节 | PDF 页 | 原书页 |")
        body.append("| --- | --- | --- |")
        for sec in c["secs"]:
            t = sec["title"].replace("|", "／")
            body.append(f"| {t} | {sec['page']}–{sec['end']} | {printed(sec['page'])}–{printed(sec['end'])} |")
        body.append("")
        body.append("## 复盘入口")
        body.append("")
        for sec in c["secs"]:
            t = re.sub(r"^[*\s]*", "", sec["title"])
            if re.search(r"归纳总结|思维拓展|疑难点|本章小结|考纲|复习提示", t):
                body.append(f"- **{t}** — PDF p{sec['page']}（原书 p.{printed(sec['page'])}）")
        body.append("")
        body.append("## 复习动作")
        body.append("")
        body.append(f"- [ ] 先看思维导图 `[[{MM[subj]}]]` 对应分支，合上书复述一遍")
        body.append(f"- [ ] 逐节精读 PDF p{c['page']}–{c['end']}，做王道课后选择题")
        body.append("- [ ] 错题丢给「Obsidian 题目复盘师」：`wd408.py` 定位 + 引页码 → `note.py --style generic` 落盘")
        body.append("")
        fname = re.sub(r'^第\s*\d+\s*章\s*', '', c['title']).replace('/', '／')
        path = f"{VAULT}/考点/{subj}/第{num}章 {fname}.md"
        open(path, "w").write("\n".join(body))
    subject_lines.append((subj, chs))

# 科目总览
for subj, chs in subject_lines:
    s = next(x for x in data if x["subject"] == subj)
    L = ["---", "type: kaodian-index", f"subject: {subj}", "tags: [408, 考点总览]", "---", "",
         f"# {subj} · 考点总览", "",
         f"> 教材：`{s['book']}` · {s['pages']} 页（扫描版，已 OCR 入索引）",
         f"> 图解：[[{MM[subj]}]] · 总览：[[408 总览]]", "",
         "| 章 | 页面（PDF / 原书） | 页数 |", "| --- | --- | --- |"]
    for c in chs:
        num = re.match(r"^第\s*(\d+)\s*章", c["title"]).group(1)
        name = re.sub(r"^第\s*\d+\s*章\s*", "", c["title"]).replace("/", "／")
        L.append(f"| [[第{num}章 {name}]] | PDF {c['page']}–{c['end']} / 原书 p.{printed(c['page'])}–{printed(c['end'])} | {c['end']-c['page']+1} |")
    L.append("")
    open(f"{VAULT}/考点/{subj}·考点总览.md", "w").write("\n".join(L))

# 408 总览
L = ["---", "type: index", "tags: [408, 考研, 索引]", "---", "",
     "# 408 · 王道教材库总览", "",
     "四本 2027 王道复习指导 + 四份思维导图，已 OCR 建索引，供「Obsidian 题目复盘师」做**页码级引用**。", "",
     "| 科目 | 教材 | 页数 | 章数 | 考点页 |", "| --- | --- | --- | --- | --- |"]
for subj, chs in subject_lines:
    s = next(x for x in data if x["subject"] == subj)
    L.append(f"| {subj} | `{s['book']}` | {s['pages']} | {len(chs)} | [[{subj}·考点总览]] |")
L += ["", "## 怎么用（复盘工作流）", "",
      "```bash", "S=/Users/jiarun/.dsh/skills/obsidian-exam-recap/scripts",
      "# 1) 找考点所在页（教材 PDF 已索引，vault=王道408）",
      'python3 $S/kb.py find "快表 页表 有效访问时间" -k 6 --kind pdf',
      "# 2) 取原话 + 双页码",
      'python3 $S/cite.py "页表 快表" -k 3',
      "# 3) 攒 JSON 一次落盘成复盘笔记",
      "python3 $S/note.py /tmp/recap.json --open", "```", "",
      "**页码换算**：四本书统一 `原书页 = PDF 页 − 12`。复盘笔记里永远写「PDF 第 N 页（原书 p.M）」。", "",
      "## 目录结构", "",
      "```",
      "王道408/",
      "  00 教材/            4 本 PDF（扫描版，带书签）",
      "  01 思维导图/        5 份 PDF + 文字版/ 目录（结构化 md）",
      "  考点/            <科目>/第N章 *.md（章节卡）+ <科目>·考点总览.md",
      "  02 章节笔记/        平时的听课/刷题笔记落这里",
      "```", "",
      "> OCR 转录有噪声（公式、上下标尤其），引用前按上下文校正；拿不准就看原页图。"]
open(f"{VAULT}/408 总览.md", "w").write("\n".join(L))
print("done")
