#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check data reproducibility, the delivered file set, and actual PDF text extraction."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / 'scripts/check_data.py')], check=True)
    expected = ['README.md', 'LICENSE.md', 'problem.tex', 'problem.pdf',
                'review/research_review.md', 'review/independent_review.md',
                'review/quality_report.md', 'scripts/generate_data.py',
                'scripts/check_data.py', 'scripts/build_pdf.py', 'scripts/check_submission.py']
    for name in expected:
        if not (root / name).is_file() or (root / name).stat().st_size == 0:
            raise SystemExit(f'Missing or empty deliverable: {name}')
    leftovers = [str(p.relative_to(root)) for p in root.rglob('*')
                 if p.is_file() and (p.suffix in {'.pyc', '.aux', '.log', '.out', '.xdv'}
                                     or p.name.startswith('.'))]
    if leftovers:
        raise SystemExit('Unwanted intermediate files: ' + ', '.join(leftovers))
    source = (root / 'problem.tex').read_text(encoding='utf-8')
    for name in re.findall(r'\\filepath\{([^}]+)\}', source):
        if ',' not in name and name.endswith(('.csv', '.json', '.md')):
            candidate = root / name if '/' in name else root / 'data' / name
            if not candidate.is_file():
                raise SystemExit('Statement attachment missing: ' + name)
    for tool in ['pdfinfo', 'pdftotext']:
        if not shutil.which(tool):
            raise SystemExit(f'{tool} (Poppler) is required for the PDF checks.')
    pdf = root / 'problem.pdf'
    info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE).group(1))
    text = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
    for phrase in ['低用水片区', '研究任务', '168', '120', '监测', '瓶试']:
        if phrase not in text:
            raise SystemExit('PDF text extraction lost expected content: ' + phrase)
    if '\ufffd' in text or not 3 <= pages <= 8:
        raise SystemExit('PDF encoding or page count needs review.')
    print(json.dumps({'submission': 'PASS', 'pdf_pages': pages,
                      'pdf_text_extraction': 'PASS',
                      'attachment_references': 'PASS', 'intermediate_files': 'NONE'},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
