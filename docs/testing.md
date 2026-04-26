# Testing

Use the repo-local Python environment in `./.conda`.

## Canonical Verification Commands

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
./.conda/bin/mkdocs build --strict
```

The test suite should remain TeX-free. LaTeX layout and staged TeX validation
belong in `pubify-tex`.
