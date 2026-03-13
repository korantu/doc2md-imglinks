from pathlib import Path

from doc2md_imglinks import convert


def test_convert_smoke(tmp_path: Path):
    pdf = Path(__file__).resolve().parents[2] / ".openclaw" / "media" / "inbound" / "seal_costing---75c0137d-9b2f-4b81-be9f-aa8796e221ea.pdf"
    if not pdf.exists():
        # In CI / clean clones, we won't have the inbound PDF.
        return

    out_dir = tmp_path / "out"
    md_path = convert(pdf, out_dir=out_dir, extract_page_renders=False)

    text = md_path.read_text(encoding="utf-8")
    assert "Seal Project Costing" in text
