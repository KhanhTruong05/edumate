from docx import Document
from docx.shared import Cm, Pt

from app.core.errors import DomainError
from app.domain.policies import require_access, require_revision
from app.domain.quality import plain_text


def add_inline(paragraph, node):
    if node.get('type') == 'text':
        run = paragraph.add_run(node.get('text', ''))
        marks = {m['type'] for m in node.get('marks', [])}
        run.bold = 'bold' in marks
        run.italic = 'italic' in marks
        run.underline = 'underline' in marks
        run.font.strike = 'strike' in marks
    elif node.get('type') == 'hardBreak':
        paragraph.add_run().add_break()
    else:
        for child in node.get('content', []):
            add_inline(paragraph, child)


def add_blocks(document, nodes):
    for node in nodes:
        kind = node.get('type')
        if kind == 'table':
            rows = node.get('content', [])
            cols = max((len(row.get('content', [])) for row in rows), default=0)
            if rows and cols:
                table = document.add_table(rows=len(rows), cols=cols)
                table.style = 'Table Grid'
                for r, row in enumerate(rows):
                    for c, cell in enumerate(row.get('content', [])):
                        table.cell(r, c).text = plain_text(cell)
        elif kind in {'bulletList', 'orderedList'}:
            for item in node.get('content', []):
                paragraph = document.add_paragraph(style='List Bullet' if kind == 'bulletList' else 'List Number')
                add_inline(paragraph, item)
        else:
            if kind == 'heading':
                level = node.get('attrs', {}).get('level', 2)
                level = level if isinstance(level, int) and 1 <= level <= 3 else 2
                paragraph = document.add_heading(level=level)
            else:
                paragraph = document.add_paragraph()
            add_inline(paragraph, node)


def render_docx(doc, destination):
    result = Document()
    section = result.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(2), Cm(2)
    section.left_margin, section.right_margin = Cm(2.5), Cm(2)
    normal = result.styles['Normal']
    normal.font.name, normal.font.size = 'Times New Roman', Pt(13)
    normal.paragraph_format.line_spacing = 1.15
    result.add_heading(doc['title'], 0)
    result.add_paragraph(f"Người soạn: {doc['owner_name']} · Phiên bản: {doc['version_no']}")
    add_blocks(result, doc['content'].get('content', []))
    section.footer.paragraphs[0].text = 'EduMate — bản mẫu; phê duyệt được theo dõi riêng trong hệ thống.'
    result.save(destination)


def create_export(db, storage, actor, identity, expected):
    with db.transaction() as tx:
        doc = tx.get('documents', identity)
        require_access(actor, doc)
        require_revision(doc['revision'], expected)
        if doc.get('export'):
            return doc
        if doc['status'] != 'draft' or doc['owner_id'] != actor['id']:
            raise DomainError('EXPORT_NOT_AVAILABLE', 'Không có bản xuất đã gắn với hồ sơ.', 409)
    # Render outside the transaction; recheck revision before attaching the artifact.
    key = storage.write_docx(lambda path: render_docx(doc, path))
    with db.transaction() as tx:
        current = tx.get('documents', identity)
        require_revision(current['revision'], expected)
        if current['status'] != 'draft':
            raise DomainError('INVALID_STATUS', 'Hồ sơ đã đổi trạng thái.', 409)
        current['export'] = {'file_key': key, 'content_hash': doc['content_hash'],
                             'document_revision': expected}
        tx.put('documents', current)
        tx.audit(actor, 'document.exported', identity, None, current['export'])
        return current
