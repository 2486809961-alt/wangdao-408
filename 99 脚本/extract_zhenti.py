#!/usr/bin/env python3
"""从王道四本书 OCR 文本里抽「历年真题 ↔ 考点」关系"""
import sqlite3, json, re, os

DB = "/Users/jiarun/.dsh/skills/obsidian-exam-recap/index/kb.db"
IDX = json.load(open("/tmp/wd_index.json"))
BOOK2SUBJ = {s["book"]: s for s in IDX}

RE_ZT = re.compile(r"考点追踪[^\u4e00-\u9fa5A-Za-z]{0,6}([^\n（(]{2,32})[（(](20\d{2}[^）)]{0,40})[）)]")
RE_ZI = re.compile(r"[【\[]\s*(20\d{2})\s*统考真题\s*[】\]]\s*([^\n]{0,180})")
RE_YEAR = re.compile(r"20\d{2}")

def chapter_of(subj, page):
    for c in subj["chapters"]:
        if c["page"] <= page <= c["end"]:
            return c["title"]
    return None

def main():
    con = sqlite3.connect(DB, timeout=60)
    con.execute("PRAGMA busy_timeout=60000")
    out = []
    for did, path, title in con.execute(
            "SELECT id,path,title FROM docs WHERE vault='王道408' AND kind='pdf'"):
        base = os.path.splitext(os.path.basename(path))[0]
        s = None
        for b, rec in BOOK2SUBJ.items():
            if os.path.splitext(os.path.basename(b))[0] == base or base in b or b in base:
                s = rec
                break
        if not s:
            continue
        for loc, text in con.execute("SELECT loc,text FROM chunks WHERE doc_id=? ORDER BY CAST(SUBSTR(loc,2) AS INTEGER)", (did,)):
            pg = int(loc[1:])
            ch = chapter_of(s, pg)
            if not ch:
                continue
            flat = re.sub(r"\s+", " ", text)
            for m in RE_ZT.finditer(flat):
                name = m.group(1).strip(" ▶>＞·—-")
                years = sorted(set(RE_YEAR.findall(m.group(2))))
                if not years:
                    continue
                out.append({"kind": "track", "subject": s["subject"], "chapter": ch,
                            "pdf_page": pg, "printed": pg - 12, "name": name,
                            "years": years, "desc": m.group(0)[:120]})
            for m in RE_ZI.finditer(flat):
                y = m.group(1)
                stem = m.group(2).strip()
                out.append({"kind": "zhenti", "subject": s["subject"], "chapter": ch,
                            "pdf_page": pg, "printed": pg - 12, "year": y, "stem": stem})
    json.dump(out, open("/tmp/wd_zhenti.json", "w"), ensure_ascii=False)
    tr = [o for o in out if o["kind"] == "track"]
    zt = [o for o in out if o["kind"] == "zhenti"]
    print("track", len(tr), "zhenti-raw", len(zt))
    from collections import Counter
    print("真题年份分布:", sorted(Counter(o["year"] for o in zt).items()))

if __name__ == "__main__":
    main()
