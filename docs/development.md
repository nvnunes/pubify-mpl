# Development

The canonical local environment is the repo-local `./.conda`.

```bash
./.conda/bin/pip install -e ".[dev]"
```

Run tests with:

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
```

Build docs with:

```bash
./.conda/bin/mkdocs build --strict
```

Keep TeX asset, template, and named-layout work in `pubify-tex`.
