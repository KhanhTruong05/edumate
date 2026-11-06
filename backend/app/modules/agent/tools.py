"""Read-only tools exposed to the orchestrator. No approve/sign tool is provided."""
from app.domain.policies import require_access
from app.domain.quality import plain_text
from app.core.errors import DomainError


def collect_sources(db, actor, source_ids: list[str]) -> list[dict]:
    sources = []
    with db.transaction() as tx:
        for identity in dict.fromkeys(source_ids):
            doc = tx.get('documents', identity)
            require_access(actor, doc)
            for index, block in enumerate(doc['content'].get('content', [])):
                text = plain_text(block).strip()
                if text:
                    sources.append({'id': f'{doc["id"]}:{doc["revision"]}:b{index}',
                                    'document_id': doc['id'], 'content_hash': doc['content_hash'],
                                    'source_status': doc['status'], 'text': text})
    if sum(len(s['text']) for s in sources) > 45000:
        raise DomainError('SOURCE_TOO_LONG', 'Tập nguồn quá dài cho bản starter; chọn ít tài liệu hơn.', 422)
    return sources
