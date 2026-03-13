from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import typer
from rich.console import Console

app = typer.Typer(add_completion=False, help="Convert PDFs to Markdown and extract embedded images with relative links.")
console = Console()


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "doc"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


@app.command("convert")
def convert(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Input PDF file"),
    out_dir: Path = typer.Option(Path("out"), "--out", "-o", help="Output directory"),
    md_name: Optional[str] = typer.Option(None, "--md", help="Markdown filename (defaults to <pdf>.md)"),
    images_dirname: str = typer.Option("images", "--images-dir", help="Subdir for extracted images"),
    dpi: int = typer.Option(200, "--dpi", min=72, max=600, help="DPI for page render fallback"),
    extract_page_renders: bool = typer.Option(
        False,
        "--render-pages",
        help="Also render each page to an image (useful for scanned PDFs).",
    ),
) -> Path:
    """Convert a PDF to Markdown and extract images.

    Notes:
    - Text extraction is best-effort (depends on PDF content).
    - Images are extracted as embedded raster images when present.
    """

    out_dir = out_dir.resolve()
    _ensure_dir(out_dir)

    base = _slug(input_path.stem)
    md_path = out_dir / (md_name or f"{base}.md")
    images_dir = out_dir / images_dirname
    _ensure_dir(images_dir)

    doc = fitz.open(str(input_path))

    lines: list[str] = []
    lines.append(f"# {input_path.stem}\n")
    lines.append(f"_Source: `{input_path.name}`_\n")

    img_count = 0

    for i in range(doc.page_count):
        page = doc.load_page(i)
        page_no = i + 1
        lines.append(f"\n---\n\n## Page {page_no}\n")

        text = page.get_text("text").strip()
        if text:
            lines.append(text + "\n")
        else:
            lines.append("_No extractable text on this page._\n")

        # Extract embedded images (best-effort)
        image_list = page.get_images(full=True)
        if image_list:
            lines.append("\n**Images**\n")
        for j, img in enumerate(image_list, start=1):
            xref = img[0]
            try:
                extracted = doc.extract_image(xref)
            except Exception as e:  # pragma: no cover
                console.print(f"[yellow]WARN[/yellow] Could not extract image xref={xref} on page {page_no}: {e}")
                continue

            ext = extracted.get("ext", "png")
            img_bytes = extracted.get("image")
            if not img_bytes:
                continue

            img_count += 1
            img_filename = f"page-{page_no:03d}-img-{j:02d}.{ext}"
            img_path = images_dir / img_filename
            img_path.write_bytes(img_bytes)

            rel = f"{images_dirname}/{img_filename}"
            lines.append(f"- ![]({rel})\n")

        if extract_page_renders:
            pix = page.get_pixmap(dpi=dpi)
            render_filename = f"page-{page_no:03d}.png"
            render_path = images_dir / render_filename
            pix.save(str(render_path))
            rel = f"{images_dirname}/{render_filename}"
            lines.append("\n**Page render**\n")
            lines.append(f"![]({rel})\n")

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    console.print(f"[green]OK[/green] Wrote {md_path}")
    console.print(f"[green]OK[/green] Extracted {img_count} embedded images to {images_dir}")
    if extract_page_renders:
        console.print(f"[green]OK[/green] Rendered {doc.page_count} pages")

    return md_path


def main() -> None:
    app()
