from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "CIVICGUIDE_IEEE_REPORT.md"
OUTPUT = ROOT / "CIVICGUIDE_IEEE_REPORT.docx"


def shade(cell, fill="EDEDED"):
    props = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    props.append(element)


def add_placeholder(doc, title, caption, url, image=None):
    if image and image.exists():
        doc.add_picture(str(image), width=Inches(6.2))
        picture = doc.paragraphs[-1]
        picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_paragraph = doc.add_paragraph()
        caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_paragraph.add_run(f"{title}\n").bold = True
        caption_paragraph.add_run(f"{caption}\nSource: {url}\nCapture date: 2026-09-15").font.size = Pt(8)
        return
    table = doc.add_table(rows=1, cols=1)
    table.autofit = True
    cell = table.cell(0, 0)
    shade(cell, "F2F4F8")
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"SCREENSHOT TO INSERT\n{title}\n\n")
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(80, 80, 80)
    detail = p.add_run(f"{caption}\nSource: {url}\nCapture date: 2026-09-15")
    detail.font.size = Pt(9)
    detail.font.color.rgb = RGBColor(100, 100, 100)
    doc.add_paragraph()


def add_markdown_line(doc, line):
    if not line.strip():
        return
    if line.startswith("# "):
        p = doc.add_heading(line[2:].strip(), level=0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif line.startswith("## "):
        doc.add_heading(line[3:].strip(), level=1)
    elif line.startswith("### "):
        doc.add_heading(line[4:].strip(), level=2)
    elif line.startswith("> "):
        p = doc.add_paragraph(style="Intense Quote")
        p.add_run(line[2:].strip())
    elif re.match(r"^\d+\. ", line):
        doc.add_paragraph(re.sub(r"^\d+\. ", "", line), style="List Number")
    elif line.startswith("* ") or line.startswith("- "):
        doc.add_paragraph(line[2:].strip(), style="List Bullet")
    elif line.startswith("|"):
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if all(set(x) <= {"-", ":"} for x in parts):
            return
        table = getattr(doc, "_active_table", None)
        if table is None or len(table.rows) > 0:
            table = doc.add_table(rows=1, cols=len(parts))
            doc._active_table = table
        else:
            table.add_row()
        row = table.rows[-1]
        for i, value in enumerate(parts):
            row.cells[i].text = re.sub(r"[*`]", "", value)
    elif line.startswith("```"):
        return
    else:
        doc.add_paragraph(re.sub(r"[`*_]", "", line.strip()))


def main():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    styles = doc.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"].font.size = Pt(10)
    styles["Heading 1"].font.name = "Times New Roman"
    styles["Heading 2"].font.name = "Times New Roman"

    in_code = False
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            p = doc.add_paragraph()
            p.style = "No Spacing"
            run = p.add_run(line)
            run.font.name = "Courier New"
            run.font.size = Pt(8)
        else:
            add_markdown_line(doc, line)
        if not line.startswith("|"):
            doc._active_table = None

    doc.add_page_break()
    doc.add_heading("Embedded Website Evidence", level=1)
    doc.add_paragraph(
        "The following evidence is tied to the running local CivicGuide application. "
        "The boxes are intentionally marked for screenshot insertion so that the final "
        "paper does not misrepresent an uncaptured or reconstructed third-party website image."
    )
    add_placeholder(
        doc,
        "Figure E1. CivicGuide landing and search interface",
        "Natural-language query box, eligibility-first headline, category filters, and navigation.",
        "http://localhost:3000/",
        ROOT / "civicguide-home.png",
    )
    add_placeholder(
        doc,
        "Figure E2. Ranked recommendation cards",
        "Use the query: I am a 22 year old unemployed woman in Chennai, Tamil Nadu looking for skill training and a small business loan.",
        "http://localhost:3000/",
        ROOT / "civicguide-results.png",
    )
    add_placeholder(
        doc,
        "Figure E3. Explanation drawer",
        "Open Why this recommendation? to show satisfied, missing, and failed rule traces plus trust metadata.",
        "http://localhost:3000/",
        ROOT / "civicguide-explanation.png",
    )
    add_placeholder(
        doc,
        "Figure E4. Backend API documentation",
        "FastAPI Swagger documentation for the implemented API routes.",
        "http://127.0.0.1:8000/docs",
    )
    doc.add_heading("Official Website Evidence", level=1)
    doc.add_paragraph(
        "Capture official government pages live, record the access date, and insert the images below. "
        "Do not recreate logos, layouts, or page content from memory. Check the portal's terms and the conference figure policy."
    )
    for title, url in [
        ("Figure E5. PM-KISAN official information page", "https://pmkisan.gov.in/"),
        ("Figure E6. Tamil Nadu UYEGP official information/application page", "https://www.msmeonline.tn.gov.in/uyegp/"),
        ("Figure E7. PM-JAY official information page", "https://nha.gov.in/PM-JAY"),
    ]:
        add_placeholder(doc, title, "Live official portal capture required before submission.", url)

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()