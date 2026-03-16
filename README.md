# doc2md-imglinks

Convert PDFs to Markdown and extract embedded images, linking them from the Markdown output using relative paths.

## Install / run (uv)

```bash
uv sync
uv run doc2md-imglinks path/to/input.pdf -o out/
```

## Example

```bash
uv run doc2md-imglinks ./seal_costing.pdf -o ./out --render-pages
```

Outputs:
- `out/<pdfname>.md`
- `out/images/` (embedded images, and optionally page renders)
