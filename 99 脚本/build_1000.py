#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""王道408 → 1000 题结构：章节目录 + 每题一篇 + ZZ 考点 + 00 索引"""
import json, os, re, shutil, collections
from blocks import block_of

VAULT = "/Users/jiarun/Documents/王道408"
OFF = 12
PREFIX = {"数据结构": "S", "计算机组成原理": "Z", "操作系统": "O", "计算机网络": "N"}
data = json.load(open("/tmp/wd_questions.json"))
idx = json.load(open("/tmp/wd_index.json"))
kds = json.load(open("/tmp/wd_kaodian.json"))["kaodian"]
tracks = [o for o in json.load(open("/tmp/wd_zhenti.json")) if o["kind"] == "track"]
OCR_FIX = [("二又", "二叉"), ("美键字", "关键字"), ("顺厚", "顺序"), ("厚序", "顺序"),
           ("顺宇表", "顺序表"), ("有厚", "有序"), ("停线性表", "序线性表")]


def fix(t):
    for a, b in OCR_FIX:
        t = t.replace(a, b)
    return t


def chnum(ch):
    return int(re.match(r"^第\s*(\d+)\s*章", ch).group(1))


def chname(ch):
    return re.sub(r"^第\s*\d+\s*章\s*", "", ch).replace("/", "／")


def folder(subj, ch):
    return f"{PREFIX[subj]}{chnum(ch):02d} {subj} 第{chnum(ch):02d}章 {chname(ch)}"


def clean_kd(name):
    n = re.sub(r"^[）)】\s]*", "", name)
    n = re.sub(r"(相关|的)?年份$", "", n)
    n = re.sub(r"[（(].*$", "", n)
    return fix(n.strip())[:34].replace("/", "／").replace("[", "(").replace("]", ")")


OPT_RE = re.compile(r"^\s*([A-D])\s*[.、．)）]\s*(.*)$")
ZHENTI_RE = re.compile(r"【\s*(20\d{2})\s*统考真题\s*】")


def q_title(subj, ch, seq):
    return f"第{chnum(ch)}章 第{seq:02d}题"


# ---------- 1. 按章分组（保持节顺序）
chapters = collections.OrderedDict()
sec_meta = {(s["subject"], s["chapter"], s["sec"]): s for s in data}
for s in data:
    key = (s["subject"], s["chapter"])
    chapters.setdefault(key, []).append(s)

CH = {(s["subject"], c["title"]): c for s in idx for c in s["chapters"]}

kd_by_chap = collections.defaultdict(list)
for k in kds:
    for ch in k["chapters"]:
        kd_by_chap[(k["subject"], ch)].append(k)


SEC = {(x["subject"], x["sec"]): x for x in json.load(open("/tmp/wd_sections.json"))}


STOP = {"查找", "分析", "应用", "计算", "特点", "比较", "基本", "相关", "各种", "排序",
        "结构", "存储", "时间", "复杂", "算法", "方法", "概念", "过程", "原理", "实现", "操作"}


def grams(t):
    t = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", t)
    return {t[i:i + 2] for i in range(len(t) - 1)} - STOP


def match_kds(subj, ch, sec_title, stem, n=2):
    """题干预 本节考点做 2-gram 重叠匹配；不够则退回本节最靠前的考点"""
    sec_list = sec_kds(subj, ch, sec_title, n=99)
    if not sec_list:
        return []
    sg = grams(stem)
    scored = []
    for nm, k in sec_list:
        ov = len(sg & grams(nm))
        scored.append((ov, len(k["years"]), nm, k))
    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    hit = [(nm, k) for ov, _, nm, k in scored if ov >= 2][:n]
    if hit:
        return hit
    top = scored[0]
    return [(top[2], top[3])] if top[0] > 0 else []


def sec_kds(subj, ch, sec_title, n=3):
    """同一节正文里出现的考点追踪 → 本节的考点（按年份数排序）"""
    r = SEC.get((subj, sec_title))
    if not r:
        return []
    lo, hi = r["page"], r["end"]
    cand, seen = [], set()
    for k in kd_by_chap.get((subj, ch), []):
        ps = [p for p in k["pages"] if lo <= p <= hi]
        if not ps:
            continue
        nm = clean_kd(k["name"])
        if nm in seen:
            continue
        seen.add(nm)
        cand.append((min(ps), -len(k["years"]), nm, k))
    cand.sort(key=lambda t: (t[1], t[0], t[2]))
    return [(nm, k) for _, _, nm, k in cand[:n]]


kd_questions = collections.defaultdict(list)
stats = collections.Counter()

for (subj, ch), secs in chapters.items():
    fdir = f"{VAULT}/{folder(subj, ch)}"
    qdir = f"{fdir}/题目"
    os.makedirs(qdir, exist_ok=True)
    rows = []
    seq = 0
    for s in secs:
        qs = sorted([q for q in s["questions"]],
                    key=lambda q: (0 if q["qtype"] == "选择" else 1, q["no"]))
        for q in qs:
            seq += 1
            title = q_title(subj, ch, seq)
            stem = fix(q["stem"])
            ans = q["answer"]
            letter, expl = "", ""
            if q["qtype"] == "选择" and ans:
                parts = ans.split("\n", 1)
                letter, expl = parts[0].strip(), (parts[1] if len(parts) > 1 else "")
            else:
                expl = re.sub(r"^【解答】\s*", "", ans or "")
            kdlinks = match_kds(subj, ch, s["sec"], fix(q["stem"]))
            tags = ["408", subj, chname(ch)]
            blk, _ = block_of(subj, chnum(ch))
            fm = ["---", "type: question", "book: 王道408", f"subject: {subj}",
                  f'block: "{blk}"',
                  f"chapter: {chnum(ch)}", f'chapter_name: "{chname(ch)}"',
                  f"no: {seq}", f"qtype: {q['qtype']}", f'sec: "{s["sec"]}"',
                  f"orig_no: {q['no']}", f"shiti_page: {q['page']}",
                  f"shiti_printed: {q['page'] - OFF}"]
            if q["answer_page"]:
                fm += [f"jiexi_page: {q['answer_page']}", f"jiexi_printed: {q['answer_page'] - OFF}"]
            fm += ["difficulty: 0", "status: 未做",
                   "topic: [" + ", ".join('"%s"' % k[0] for k in kdlinks) + "]",
                   "tags: [" + ", ".join(tags) + "]", "---"]
            blk_q, _ = block_of(subj, chnum(ch))
            body = fm + ["", f"# {title}", "",
                         '<div class="wd-head">' +
                         f'<span class="wd-badge">{subj} · 第{chnum(ch):02d}章 · {seq:02d}</span>'
                         f'<span class="wd-chip qtype-{q["qtype"]}">{q["qtype"]}题</span>'
                         f'<span class="wd-chip">{s["sec"]}</span>'
                         f'<span class="wd-chip">{blk_q}</span>'
                         + (f'<span class="wd-chip">真题 {ZHENTI_RE.search(q["stem"]).group(1)}</span>'
                            if ZHENTI_RE.search(q["stem"]) else "") +
                         '</div>', ""]
            # 题干 + 选项
            stem_lines = stem.splitlines()
            opts, rest = [], []
            for ln in stem_lines:
                m = OPT_RE.match(ln)
                if m:
                    opts.append((m.group(1), m.group(2).strip()))
                elif opts or rest:
                    if opts and not OPT_RE.match(ln) and ln.strip():
                        # 选项后的续行并入最后一个选项
                        k, v = opts[-1]
                        opts[-1] = (k, v + ln.strip())
                    elif not opts:
                        rest.append(ln)
                else:
                    rest.append(ln)
            body.append("> [!question] 题干")
            for ln in rest:
                if ln.strip():
                    body.append(f"> {ln}")
            if opts:
                body += ["> <div class=\"wd-opts\">"]
                for k, v in opts:
                    body.append(f'> <div class="wd-opt"><b>{k}</b><span>{v}</span></div>')
                body.append("> </div>")
            body.append("")
            if letter:
                body += ["> [!success] 答案", f'> <span class="wd-ans">{letter}</span>', ""]
            if expl:
                body += ["## 解析要点", "", '<div class="wd-expl">', ""]
                t = fix(expl)
                t = re.sub(r"\n+", "", t)
                for seg in [x.strip() for x in re.split(r"(?=(?:\d{1,2}[）)]|【|考点追踪))", t) if x.strip()]:
                    body += [seg, ""]
                body += ["</div>", ""]
            if kdlinks:
                body.append("> [!info] 考点")
                body.append("> <div class=\"wd-chips\">")
                for name, k in kdlinks:
                    body.append(f'> [[ZZ 考点/{name}\\|{name}]]')
                body.append("> </div>")
                body += [">", f"> 本章复盘：[[{folder(subj, ch)}/本章复盘|{ch}]]", ""]
            pages = f'<span class="wd-page">题目 PDF p{q["page"]} · 原书 p{q["page"]-OFF}</span>'
            if q["answer_page"]:
                pages += f'<span class="wd-page">解析 PDF p{q["answer_page"]} · 原书 p{q["answer_page"]-OFF}</span>'
            body += ["> [!example] 教材出处",
                     f"> 《王道 {subj}》{ch} · {s['sec']}",
                     f"> <div class=\"wd-pages\">{pages}</div>", ""]
            body += ["> [!warning] 复盘提示",
                     "> - [ ] 先自己重做一遍，再看解析",
                     "> - [ ] 卡住的第一步写进 `ZZ 错题复盘/`",
                     ""]
            path = f"{qdir}/{title}.md"
            open(path, "w").write("\n".join(body) + "\n")
            link = f"{folder(subj, ch)}/题目/{title}"
            for name, k in kdlinks:
                kd_questions[name].append((subj, ch, seq, link))
            rows.append({"seq": seq, "qtype": q["qtype"], "sec": s["sec"], "page": q["page"],
                         "apage": q["answer_page"], "letter": letter,
                         "kd": "、".join(k[0] for k in kdlinks), "link": link,
                         "orig": q["no"]})
            stats[subj] += 1

    # 本章复盘
    info = CH[(subj, ch)]
    kd_chap_pre = None
    sel_n = sum(1 for r in rows if r["qtype"] == "选择")
    blk_c, blk_d = block_of(subj, chnum(ch))
    info0 = CH[(subj, ch)]
    kd_chap_pre = [k for k in kds if k["subject"] == subj and ch in k["chapters"]]
    L = ["---", "type: chapter", f"subject: {subj}", f'block: "{blk_c}"',
         f"chapter: {chnum(ch)}",
         f'chapter_name: "{chname(ch)}"', f"questions: {len(rows)}",
         f"tags: [408, {subj}, {chname(ch)}]", "---", "",
         f"# {ch} · 本章复盘", "",
         f"> 教材：`00 教材/` · PDF 第 {info['page']}–{info['end']} 页（原书 p.{info['page']-OFF}–{info['end']-OFF}）",
         f"> 本章共 **{len(rows)} 题**（选择 {sel_n} / 综合 {len(rows)-sel_n}），题号 1–{len(rows)} 连续。",
         f"> 大类：[[ZZ 大类/{subj} · {blk_c.replace('/', '／')}|{blk_c}]]（{blk_d}）",
         f"> 图谱：[[408 大类网]] · [[408 知识网·全科]] · 返回：[[408 MOC]]", "",
         '<div class="wd-stat">' +
         f'<div><b>{len(rows)}</b><span>本章题数</span></div>' +
         f'<div><b>{sel_n}</b><span>选择题</span></div>' +
         f'<div><b>{len(rows)-sel_n}</b><span>综合题</span></div>' +
         f'<div><b>{len(kd_chap_pre)}</b><span>标注考点</span></div>' +
         '</div>', "",
         "## 小节与页码", "", "| 小节 | PDF 页 | 原书页 |", "| --- | --- | --- |"]
    for sec in info["secs"]:
        L.append(f"| {sec['title']} | {sec['page']}–{sec['end']} | {sec['page']-OFF}–{sec['end']-OFF} |")
    L += ["", "## 题目清单", "", "| 题号 | 题型 | 节 | 考点 | 题目页 | 解析页 | 答案 |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        L.append(f"| [[{r['link']}|第{r['seq']:02d}题]] | {r['qtype']} | {r['sec']} | {r['kd']} | "
                 f"p{r['page']} | {'p'+str(r['apage']) if r['apage'] else '—'} | {r['letter'] or '—'} |")
    kd_chap = sorted(kd_by_chap.get((subj, ch), []), key=lambda k: -len(k["years"]))
    if kd_chap:
        L += ["", "## 历年真题分布（王道标注）", "", "| 考点 | 真题年份 |", "| --- | --- |"]
        for k in kd_chap:
            nm = clean_kd(k["name"])
            L.append(f"| [[ZZ 考点/{nm}\\|{nm}]] | {'、'.join(k['years'])} |")
    open(f"{fdir}/本章复盘.md", "w").write("\n".join(L) + "\n")

print("题目笔记:", sum(stats.values()), dict(stats))

# ---------- 2. ZZ 考点
os.makedirs(f"{VAULT}/ZZ 考点", exist_ok=True)
kd_meta = {}
for k in kds:
    nm = clean_kd(k["name"])
    r = kd_meta.setdefault(nm, {"subjects": set(), "chapters": set(), "years": set(), "pages": set()})
    r["subjects"].add(k["subject"]); r["chapters"].update(k["chapters"])
    r["years"].update(k["years"]); r["pages"].update(k["pages"])

for nm, r in kd_meta.items():
    qs = kd_questions.get(nm, [])
    subj_s = "、".join(sorted(r["subjects"]))
    L = ["---", "type: kaodian", f'name: "{nm}"', f"subject: {subj_s}",
         f"wd_count: {len(qs)}", "years: [" + ", ".join(sorted(r["years"])) + "]",
         "vault: 408", "---", "",
         f"# 考点：{nm}",
         "",
         f"> 王道四本书里标为考点的原文，**{len(qs)} 题** 挂在本页 · **{len(r['years'])} 个年份** 考过（{'、'.join(sorted(r['years']))}）。",
         "> 同一考点的题在图谱里通过本页相连。", "",
         f"## 王道题目（{len(qs)}）", "", '<div class="wd-qlist">', ""]
    if qs:
        for subj, ch, seq, link in qs:
            L.append(f"- [[{link}|{ch} · 第{seq:02d}题]]（{subj}）")
    else:
        L.append("- （本章暂无自动关联题目）")
    L += ["", "</div>", "", "## 真题年份", ""]
    if r["years"]:
        L.append('<div class="wd-chips">' +
                 " ".join(f"[[{y} 真题清单|{y}]]" for y in sorted(r["years"])) + "</div>")
        L += ["", '<div class="wd-pages">' +
              "".join(f'<span class="wd-page">PDF p{p} · 原书 p.{p-OFF}</span>' for p in sorted(r["pages"])[:5]) +
              "</div>"]
    else:
        L.append("- （无标注）")
    L += ["", "## 教材位置", ""]
    for p in sorted(r["pages"])[:5]:
        L.append(f"- PDF p{p}（原书 p.{p-OFF}）")
    safe = nm.replace('"', "")
    open(f"{VAULT}/ZZ 考点/{safe}.md", "w").write("\n".join(L) + "\n")
print("考点页:", len(kd_meta))
