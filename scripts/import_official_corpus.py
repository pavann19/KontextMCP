"""Download immutable official EUR-Lex snapshots; preserve curated corpus separately."""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import httpx
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())


def parse_html(html,language,url):
    soup=BeautifulSoup(html,"html.parser")
    result=[]
    for element in soup.find_all("div",id=re.compile(r"^(?:art_\d+|anx_[IVXLC\d]+)$",re.I)):
        identifier=element["id"]
        if not re.fullmatch(r"art_\d+|anx_[IVXLC\d]+",identifier,re.I): continue
        title=element.find(class_="eli-title")
        label=("Article " if language=="en" else "Artikel ")+identifier[4:] if identifier.startswith("art_") else ("Annex " if language=="en" else "Anhang ")+identifier[4:]
        text=element.get_text(" ",strip=True)
        result.append({"doc_id":f"official_{language}_{identifier}","language":language,"type":"article" if identifier.startswith("art_") else "annex",
            "article_id":label,"title":title.get_text(" ",strip=True) if title else label,"chapter":"Official EUR-Lex publication",
            "text":text,"keywords":[],"regulation_id":"Regulation (EU) 2024/1689","celex_uri":url,
            "publication_date":"2024-07-12","content_sha256":hashlib.sha256(text.encode()).hexdigest(),"html_element_id":identifier})
    if len([r for r in result if r["type"]=="article"]) != 113 or len([r for r in result if r["type"]=="annex"]) != 13:
        raise ValueError("Official article count mismatch or challenge/error page; snapshot rejected")
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=ROOT/"data/official")
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    report={"status":"PASS","scope":"Official publication snapshot and parser consistency; no independent legal sign-off", "languages":{},"curated_comparison":[],"human_legal_review":"UNVERIFIED"}
    for lang in ("en","de"):
        url=f"https://eur-lex.europa.eu/legal-content/{lang.upper()}/TXT/HTML/?uri=CELEX:32024R1689"
        response=httpx.get(url,follow_redirects=True,timeout=60);response.raise_for_status()
        html=response.content.decode("utf-8")
        docs=parse_html(html,lang,str(response.url))
        digest=hashlib.sha256(response.content).hexdigest()
        snapshot=args.output/(lang+"-"+digest+".html")
        if not snapshot.exists(): snapshot.write_bytes(response.content)
        (args.output/f"eu_ai_act_{lang}.json").write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding="utf-8")
        # Parse the preserved snapshot again, not metadata generated from curated text.
        assert docs==parse_html(snapshot.read_text(encoding="utf-8"),lang,str(response.url))
        report["languages"][lang]={"url":str(response.url),"html_sha256":digest,"snapshot":str(snapshot.relative_to(ROOT)) if snapshot.is_relative_to(ROOT) else str(snapshot),"articles":sum(d["type"]=="article" for d in docs),"annexes":sum(d["type"]=="annex" for d in docs),"snapshot_reparse_matches":True}
        curated=json.loads((ROOT/f"data/raw/eu_ai_act_{lang}.json").read_text(encoding="utf-8"))
        official={normalize(d["article_id"]):d for d in docs}
        for item in curated:
            match=official.get(normalize(item["article_id"]))
            score=difflib.SequenceMatcher(None,normalize(item["text"]),normalize(match["text"]) if match else "",autojunk=False).ratio()
            report["curated_comparison"].append({"language":lang,"article_id":item["article_id"],"exact_normalized_match":bool(match and normalize(item["text"])==normalize(match["text"])),"similarity":score})
    report["timestamp"]=datetime.now(timezone.utc).isoformat()
    report["curated_equivalence"]="PASS" if all(r["exact_normalized_match"] for r in report["curated_comparison"]) else "FAIL"
    output=ROOT/"artifacts/reports/official_source_comparison.json"
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"curated_equivalence":report["curated_equivalence"],"report":str(output)}))

if __name__=="__main__": main()
