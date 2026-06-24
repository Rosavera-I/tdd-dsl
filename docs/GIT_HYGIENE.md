# Git Hygiene

## Artifact Policy

Generated build outputs and dependency installs must stay out of Git.

Ignored paths:

- `dist/`
- `node_modules/`
- Python cache files and pytest cache directories

## Cleanup Verification

Checked on 2026-06-24:

- `git ls-files | rg '(^|/)(node_modules|dist)(/|$)'` returned no tracked paths.
- `find . -type d \( -name node_modules -o -name dist \) -prune -print` found no local artifact directories.
- `git log --oneline --all --name-only -- '**/node_modules/**' '**/dist/**'` returned no matching history entries in this clone.

Because no tracked `node_modules/` or `dist/` paths were present in the current index or visible history, no index removal or history rewrite was performed.

If artifact paths appear later, remove them from the index without deleting local files:

```bash
git rm -r --cached node_modules dist
```
