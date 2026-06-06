# pip install pymupdf

import fitz  # PyMuPDF

filename = "screenie"  # file name without the .pdf extension

doc = fitz.open(f"~/Downloads/{filename}.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=200)
    pix.save(f"~/Downloads/{filename}_page_{i+1}.png")