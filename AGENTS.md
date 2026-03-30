# pubify-mpl Agent Notes

Keep this file limited to non-obvious repo conventions that are likely to save time or prevent mistakes.

- `build/tex/` is a flat staged TeX workspace.
  - `scripts/build_tex_assets.py` rewrites local `\input{...}` / `\include{...}` paths in staged TeX copies so gallery/debug sources still compile after flattening.
  - TeX source basenames must stay unique across `gallery/` and `debug/`; the builder treats staged basename collisions as errors.
  - If you change relationships among `gallery/`, `debug/`, or shared TeX files, verify a real compile from `build/tex/`, not just Python tests.
- The debug TeX files have distinct purposes:
  - `debug-layout-gallery.tex`: full-gallery diagnostic entrypoint
  - `debug-subcaptions.tex`: focused subcaption-spacing fixture
- When developing TeX-side behavior, stage first and compile from `build/tex/`.
  - This keeps the staged `.tex`, `.aux`, `.fls`, `.fdb_latexmk`, and `.log` files together so you can inspect TeX warnings and `pubify` debug output in one place.
  - Example:
    - `./.conda/bin/python3.12 scripts/build_tex_assets.py debug/debug-subcaptions.tex`
    - `cd build/tex`
    - `latexmk -g -pdf -interaction=nonstopmode debug-subcaptions.tex`
- `gallery/layout-gallery.pdf` and `examples/quickstart.ipynb` are tracked generated artifacts.
  - Refresh them with `scripts/update_layout_gallery.py` and `scripts/update_quickstart_notebook.py`.
  - Do not hand-edit them.
- The built-in fallback template is public as `pubify_mpl.DEFAULT_TEMPLATE`.
  - The README quick-start block and notebook template are generated/checked against that constant, so update it first.
- If template geometry or typography seems wrong, use `\figprintlayoutspec` to measure the LaTeX side and copy those values back into the Python template configuration.
- The repo-local pre-commit hook mutates tracked files.
  - It regenerates the notebook, refreshes the gallery PDF, and runs `mkdocs build --strict`.
  - Even if you did not edit those artifacts directly, the hook may rewrite them.
- The most important repo-specific tests are:
  - `tests/test_readme.py` for README/template drift
  - `tests/test_layout.py` for Python-vs-`pubify.sty` default consistency
  - `tests/test_build_gallery.py` for staged TeX workspace behavior
- Canonical full test command:
  - `./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider`
- Practical local verification sequence after nontrivial changes:
  - run the full pytest command
  - run `sh .githooks/pre-commit`
