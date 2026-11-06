import hashlib
import json
import re

from app.core.errors import DomainError

ALLOWED_NODES = {'doc', 'paragraph', 'text', 'heading', 'bulletList', 'orderedList',
                 'listItem', 'hardBreak', 'table', 'tableRow', 'tableCell', 'tableHeader'}
ALLOWED_MARKS = {'bold', 'italic', 'underline', 'strike', 'code'}


def validate_editor(node: dict, depth: int = 0, budget: list | None = None) -> None:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if (depth == 0 and node.get('type') != 'doc') or depth > 20 or budget[0] > 6000 or node.get('type') not in ALLOWED_NODES:
        raise DomainError('INVALID_EDITOR', 'Nội dung editor không được hỗ trợ.', 422)
    if not isinstance(node.get('content', []), list):
        raise DomainError('INVALID_EDITOR', 'Cấu trúc content phải là danh sách.', 422)
    if not isinstance(node.get('attrs', {}), dict) or not isinstance(node.get('marks', []), list):
        raise DomainError('INVALID_EDITOR', 'Định dạng block không hợp lệ.', 422)
    if node.get('type') == 'text' and not isinstance(node.get('text', ''), str):
        raise DomainError('INVALID_EDITOR', 'Nội dung văn bản không hợp lệ.', 422)
    for mark in node.get('marks', []):
        if not isinstance(mark, dict) or mark.get('type') not in ALLOWED_MARKS:
            raise DomainError('INVALID_MARK', 'Định dạng chưa được hỗ trợ.', 422)
    for child in node.get('content', []):
        if not isinstance(child, dict):
            raise DomainError('INVALID_EDITOR', 'Block không hợp lệ.', 422)
        validate_editor(child, depth + 1, budget)


def plain_text(node: dict) -> str:
    if node.get('type') == 'text':
        return node.get('text', '')
    return '\n'.join(plain_text(c) for c in node.get('content', []))


def content_hash(content: dict) -> str:
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def rule_checks(document: dict) -> list[dict]:
    findings = []
    if not document['title'].strip():
        findings.append({'code': 'MISSING_TITLE', 'message': 'Thiếu tên tài liệu.', 'blocking': True})
    if len(plain_text(document['content']).strip()) < 20:
        findings.append({'code': 'SHORT_CONTENT', 'message': 'Nội dung quá ngắn để nộp.', 'blocking': True})
    if document['kind'] == 'lesson':
        text = plain_text(document['content']).lower()
        for heading in ['mục tiêu', 'hoạt động', 'đánh giá']:
            if heading not in text:
                findings.append({'code': 'CHECK_SECTION', 'message': f'Chưa tìm thấy mục “{heading}” trong nội dung editor.', 'blocking': False})
    return findings


def verify_claims(claims: list[dict], sources: list[dict]) -> list[dict]:
    index = {s['id']: s for s in sources}
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    errors = []
    for claim in claims:
        source = index.get(claim.get('source_id'))
        quote = normalize(claim.get('quote', ''))
        if source is None or not quote or quote not in normalize(source['text']):
            errors.append({'code': 'INVALID_EVIDENCE', 'message': 'Nguồn hoặc trích dẫn không khớp tập nguồn đã cấp.'})
    # Exact citations do not prove entailment. All generated content remains a draft.
    return errors
