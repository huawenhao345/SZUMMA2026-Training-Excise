#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check packet files, links, input integrity and four-page PDF text/bounds."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'README.md','LICENSE.md','problem.tex','problem.pdf',
 'data/README.md','data/stops.csv','data/links.csv','data/vehicles.csv','data/cases.csv',
 'data/passenger_requests.csv','data/link_factors.csv','data/baseline_plan.csv','data/rules.json',
 'scripts/make_inputs.py','scripts/check_inputs.py','scripts/check_plan.py',
 'scripts/check_action_log.py','scripts/build_pdf.py','scripts/check_submission.py',
 'review/research_review.md','review/quality_report.md','review/editorial_review.md','review/independent_review.md'}


def main():
    subprocess.run([sys.executable,str(ROOT/'scripts/check_inputs.py')],check=True,stdout=subprocess.PIPE,text=True)
    actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    if actual!=EXPECTED:raise SystemExit(f'File set mismatch: missing={EXPECTED-actual}; extra={actual-EXPECTED}')
    if any((ROOT/p).stat().st_size==0 for p in EXPECTED):raise SystemExit('Empty deliverable')
    source=(ROOT/'problem.tex').read_text()
    for name in re.findall(r'\\file\{([^}]+)\}',source):
        target=ROOT/name if '/' in name else ROOT/'data'/name
        if not target.is_file():raise SystemExit('Missing attachment: '+name)
    for tool in ['pdfinfo','pdftotext']:
        if not shutil.which(tool):raise SystemExit(tool+' (Poppler) is required')
    info=subprocess.check_output(['pdfinfo',str(ROOT/'problem.pdf')],text=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
    content=subprocess.check_output(['pdftotext','-layout',str(ROOT/'problem.pdf'),'-'],text=True)
    compact=re.sub(r'\s+','',content)
    for phrase in ['校园小巴的高峰运行与调度','7350','2448','7200','5400','1800','95',
                   '信息延迟','未完成','交班','模拟设定','参考资料']:
        if re.sub(r'\s+','',phrase) not in compact:raise SystemExit('PDF lost text: '+phrase)
    ptexts=[p.strip() for p in content.split('\f') if p.strip()]
    if pages!=4 or '\ufffd' in content or len(ptexts)!=4:raise SystemExit('PDF page count or text encoding mismatch')
    if content.count('数学建模训练题')!=4 or not all('审核稿' in p.splitlines()[0] for p in ptexts):raise SystemExit('Review headers missing')
    tree=ET.fromstring(subprocess.check_output(['pdftotext','-bbox-layout',str(ROOT/'problem.pdf'),'-'],text=True));words=0
    for page in tree.iter():
        if page.tag.rsplit('}',1)[-1]!='page':continue
        w,h=float(page.attrib['width']),float(page.attrib['height'])
        for word in page.iter():
            if word.tag.rsplit('}',1)[-1]!='word':continue
            words+=1;x0,y0,x1,y1=(float(word.attrib[k]) for k in ['xMin','yMin','xMax','yMax'])
            if not(20<=x0<=x1<=w-20 and 18<=y0<=y1<=h-18):raise SystemExit('PDF word outside safe boundary: '+str(word.text))
    print(json.dumps({'status':'PASS','files':len(EXPECTED),'pdf_pages':pages,'pdf_words_checked':words,'inputs_and_attachments':'PASS','unexpected_private_files':'NONE'},ensure_ascii=False))


if __name__=='__main__':main()
