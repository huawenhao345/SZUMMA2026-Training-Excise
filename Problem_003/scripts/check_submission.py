#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the delivery packet, attachment links, PDF text and physical page bounds."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'README.md', 'LICENSE.md', 'problem.tex', 'problem.pdf',
    'data/README.md', 'data/parameters.json', 'data/routes.csv',
    'data/gear_options.csv', 'data/cooling_options.csv', 'data/rules.json',
    'scripts/make_inputs.py', 'scripts/check_inputs.py', 'scripts/check_design.py',
    'scripts/build_pdf.py', 'scripts/check_submission.py',
    'review/research_review.md', 'review/quality_report.md',
    'review/independent_review.md', 'review/editorial_review.md',
}


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_inputs.py')], check=True,
                   stdout=subprocess.PIPE, text=True)
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    if actual != EXPECTED:
        raise SystemExit(f'File set mismatch: missing={EXPECTED-actual}; extra={actual-EXPECTED}')
    if any((ROOT / p).stat().st_size == 0 for p in EXPECTED):
        raise SystemExit('Empty deliverable')
    source = (ROOT / 'problem.tex').read_text(encoding='utf-8')
    for name in re.findall(r'\\file\{([^}]+)\}', source):
        target = ROOT / name if '/' in name else ROOT / 'data' / name
        if not target.is_file():
            raise SystemExit('Statement attachment missing: ' + name)
    for tool in ['pdfinfo', 'pdftotext']:
        if not shutil.which(tool):
            raise SystemExit(tool + ' (Poppler) is required')
    info = subprocess.check_output(['pdfinfo', str(ROOT / 'problem.pdf')], text=True)
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    content = subprocess.check_output(['pdftotext', '-layout', str(ROOT / 'problem.pdf'), '-'], text=True)
    for phrase in ['山地货运轨道车的无源限速', '360', '300', '100', '50',
                   '星点', '初始电角度', '瞬时绝对值', '参考资料', '0.00393']:
        if phrase not in content:
            raise SystemExit('PDF lost text: ' + phrase)
    if '\ufffd' in content or pages != 3:
        raise SystemExit('PDF encoding or page count mismatch')
    page_texts = [page.strip() for page in content.split('\f') if page.strip()]
    if content.count('数学建模训练题') != 3 or len(page_texts) != 3 or not all(
            '原创模拟题' in page.splitlines()[0] for page in page_texts):
        raise SystemExit('Submission edition headers missing')
    bbox = subprocess.check_output(['pdftotext', '-bbox-layout', str(ROOT / 'problem.pdf'), '-'], text=True)
    tree = ET.fromstring(bbox)
    words = 0
    for page in tree.iter():
        if page.tag.rsplit('}', 1)[-1] != 'page':
            continue
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        for word in page.iter():
            if word.tag.rsplit('}', 1)[-1] != 'word':
                continue
            words += 1
            x0, y0, x1, y1 = (float(word.attrib[k]) for k in ['xMin', 'yMin', 'xMax', 'yMax'])
            if not (20 <= x0 <= x1 <= width - 20 and 18 <= y0 <= y1 <= height - 18):
                raise SystemExit('PDF word outside safe page boundary: ' + (word.text or ''))
    print(json.dumps({'status': 'PASS', 'files': len(EXPECTED), 'pdf_pages': pages,
                      'pdf_words_checked': words, 'attachments_and_inputs': 'PASS',
                      'unexpected_or_private_files': 'NONE'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
