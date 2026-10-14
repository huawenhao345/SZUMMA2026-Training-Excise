#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile the contestant statement twice, keeping auxiliaries outside the repository."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    if not shutil.which('xelatex'):
        raise SystemExit('XeLaTeX is required. Install TeX Live and the Noto CJK fonts.')
    with tempfile.TemporaryDirectory(prefix='problem002-latex-') as temporary:
        temp = Path(temporary)
        env = dict(os.environ)
        env['XDG_CACHE_HOME'] = str(temp / 'cache')
        (temp / 'cache').mkdir()
        command = ['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                   f'-output-directory={temp}', 'problem.tex']
        for _ in range(2):
            result = subprocess.run(command, cwd=root, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                raise SystemExit(result.stdout[-6000:])
        log = (temp / 'problem.log').read_text(errors='replace')
        failures = re.findall(r'^.*(?:Overfull \\[hv]box|Missing character|LaTeX Font Warning).*$',
                              log, re.MULTILINE)
        if failures:
            raise SystemExit('PDF quality check failed:\n' + '\n'.join(failures))
        pdf = temp / 'problem.pdf'
        if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
            raise SystemExit('Compiler did not produce a valid PDF header.')
        shutil.copyfile(pdf, root / 'problem.pdf')
        print(f'PASS XeLaTeX (2 passes); no overflow, missing glyph, or font substitution; '
              f'PDF {pdf.stat().st_size} bytes')


if __name__ == '__main__':
    main()
