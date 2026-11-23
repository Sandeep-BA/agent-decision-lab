"""Subtree pruning versus a nested .gitignore that re-includes a file. Author: Sandeep Belgavi.

A file walker that honours .gitignore can skip a whole directory when it knows
everything inside is ignored. Turning a root pattern `logs/**` into "prune
logs/" is tempting, but `logs/**` matches what is inside logs/, not logs/
itself, so git still enters logs/, reads logs/.gitignore and lets `!keep.txt`
re-include logs/keep.txt. Directories below logs/ are themselves matched by
`logs/**`, so git does not enter them, and a negation cannot bring back a file
under an excluded directory.

Three walkers over one synthetic tree:
  git_like       models git's rules for the small pattern subset used here;
  prune_naive    prunes any `dir/**` directory without reading its .gitignore;
  prune_guarded  prunes only if no negation in the same file or in
                 <dir>/.gitignore could apply (the rule gemini-cli PR 30370
                 adopted, re-implemented independently).
`git_oracle()` asks a real git (`git status --porcelain --ignored -uall`) for
the same tree. Supported pattern subset: `name`, `name/`, `dir/**`, `!name`,
`!dir/name`, with `*` inside a segment. Not a full gitignore implementation.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
import json
import os
import shutil
import subprocess
import tempfile

TREE = {
    '.gitignore': 'logs/**\nbuild/**\n*.tmp\n',
    'logs/.gitignore': '!keep.txt\n',
    'logs/keep.txt': 'payload',
    'logs/a.txt': 'discard',
    'logs/sub/keep.txt': 'nested',
    'build/.gitignore': '# no negations here\n',
    'build/out.bin': 'x',
    'src/app.py': 'print(1)',
    'src/scratch.tmp': 'y',
}


def rules_of(text: str, base: str) -> list[tuple[str, str, bool]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        neg = line.startswith('!')
        out.append((base, line[1:] if neg else line, neg))
    return out


def matches(pattern: str, rel: str, is_dir: bool) -> bool:
    """rel is relative to the directory holding the pattern."""
    dir_only = pattern.endswith('/') and not pattern.endswith('/**')
    p = pattern.rstrip('/') if dir_only else pattern
    if dir_only and not is_dir:
        return False
    if p.endswith('/**'):
        prefix = p[:-3].lstrip('/')
        return rel.startswith(prefix + '/')          # everything inside, not the directory itself
    if '/' in p.strip('/'):
        return fnmatchcase(rel, p.lstrip('/'))
    return fnmatchcase(rel.rsplit('/', 1)[-1], p)


def ignored(path: str, is_dir: bool, rules) -> bool:
    verdict = False
    for base, pattern, neg in rules:                    # last matching rule wins
        if base and not path.startswith(base + '/'):
            continue
        rel = path[len(base) + 1:] if base else path
        if matches(pattern, rel, is_dir):
            verdict = not neg
    return verdict


def walk(tree: dict, mode: str) -> dict:
    files = sorted(tree)
    dirs = sorted({'/'.join(f.split('/')[:i]) for f in files for i in range(1, f.count('/') + 1)})
    root_rules = rules_of(tree.get('.gitignore', ''), '')
    kept, read_files, pruned = [], ['.gitignore'], []

    def visit(d: str, rules):
        if d and f'{d}/.gitignore' in tree:
            rules = rules + rules_of(tree[f'{d}/.gitignore'], d)
            read_files.append(f'{d}/.gitignore')
        for f in files:
            if f.rsplit('/', 1)[0] == d if '/' in f else d == '':
                if not ignored(f, False, rules):
                    kept.append(f)
        for sub in dirs:
            if (sub.rsplit('/', 1)[0] if '/' in sub else '') != d:
                continue
            if mode != 'git_like' and should_prune(sub, rules, tree, guarded=(mode == 'prune_guarded')):
                pruned.append(sub + '/')
                continue
            if ignored(sub, True, rules):
                pruned.append(sub + '/')
                continue
            visit(sub, rules)

    visit('', root_rules)
    return {'mode': mode, 'kept': sorted(kept), 'pruned': sorted(pruned), 'gitignores_read': sorted(read_files)}


def should_prune(d: str, rules, tree: dict, guarded: bool) -> bool:
    """Does a `<d>/**` rule let the walker skip d entirely?"""
    starred = any(not neg and pattern.rstrip('/') == (d[len(base) + 1:] if base else d) + '/**'
                  for base, pattern, neg in rules)
    if not starred:
        return False
    if not guarded:
        return True
    same_file_negation = any(neg for _, _, neg in rules)
    nested = tree.get(f'{d}/.gitignore', '')
    nested_negation = any(line.strip().startswith('!') for line in nested.splitlines())
    return not (same_file_negation or nested_negation)


def git_oracle(tree: dict = TREE) -> list[str] | None:
    """Files real git reports as not ignored, or None when git is unavailable."""
    git = shutil.which('git')
    if not git:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in tree.items():
            path = os.path.join(tmp, *rel.split('/'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
        subprocess.run([git, 'init', '-q'], cwd=tmp, check=True)
        out = subprocess.run([git, 'status', '--porcelain', '--ignored', '-uall'], cwd=tmp, check=True,
                             capture_output=True, text=True).stdout
    return sorted(line[3:] for line in out.splitlines() if line.startswith('?? '))


def run() -> dict:
    return {m: walk(TREE, m) for m in ('git_like', 'prune_naive', 'prune_guarded')} | {'git_oracle_kept': git_oracle()}


if __name__ == '__main__':
    print(json.dumps(run(), indent=1))
