#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the complete review packet, referenced attachments and real PDF extraction."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'README.md','LICENSE.md','problem.tex','problem.pdf',
 'data/README.md','data/orchard.csv','data/cultivar_genotypes.csv','data/cultivar_planning.csv',
 'data/bloom_profiles.csv','data/visitation.csv','data/movement_trials.csv',
 'data/carryover_trials.csv','data/fruit_set_trials.csv','data/scenarios.csv','data/rules.json',
 'scripts/generate_data.py','scripts/check_data.py','scripts/check_plan.py',
 'scripts/build_pdf.py','scripts/check_submission.py',
 'review/research_review.md','review/quality_report.md','review/editorial_review.md'}


def main():
    subprocess.run([sys.executable,str(ROOT/'scripts/check_data.py')],check=True)
    actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    if actual!=EXPECTED:raise SystemExit(f'File set mismatch. Missing {EXPECTED-actual}; extra {actual-EXPECTED}')
    if any((ROOT/p).stat().st_size==0 for p in EXPECTED):raise SystemExit('Empty deliverable')
    source=(ROOT/'problem.tex').read_text()
    for name in re.findall(r'\\file\{([^}]+)\}',source):
        target=ROOT/name if '/' in name else ROOT/'data'/name
        if not target.exists():raise SystemExit('Statement attachment missing: '+name)
    for tool in ['pdfinfo','pdftotext']:
        if not shutil.which(tool):raise SystemExit(tool+' (Poppler) is required for PDF validation')
    info=subprocess.check_output(['pdfinfo',str(ROOT/'problem.pdf')],text=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',info,re.MULTILINE).group(1))
    content=subprocess.check_output(['pdftotext','-layout',str(ROOT/'problem.pdf'),'-'],text=True)
    for phrase in ['苹果园的授粉安排','6000','10000','64','访花','参考资料']:
        if phrase not in content:raise SystemExit('PDF lost text: '+phrase)
    if '\ufffd' in content or not 2<=pages<=4:raise SystemExit('PDF encoding or page count needs review')
    print(json.dumps({'status':'PASS','files':len(EXPECTED),'pdf_pages':pages,
                      'attachment_references':'PASS','pdf_text_extraction':'PASS',
                      'unexpected_or_private_files':'NONE'},ensure_ascii=False))


if __name__=='__main__':main()
