from pathlib import Path

from pypdf import PdfReader, PdfWriter


def set_pdf_title(pdf_path: str | Path, title: str) -> None:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    writer.append(reader)

    metadata = reader.metadata
    if metadata is None:
        from pypdf.constants import Meta as MetaKeys
        writer.add_metadata({MetaKeys.TITLE: title})
    else:
        writer.add_metadata({"/Title": title})

    writer.write(str(pdf_path))


def postprocess(pdf_path: str | Path, title: str) -> None:
    set_pdf_title(pdf_path, title)
