from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.api.schemas import NewDocument, SaveDocument, Revision, Decision, Override, TeacherReport, DraftRequest
from app.core.errors import DomainError
from app.domain.quality import rule_checks
from app.modules.auth.service import current_user
from app.modules.documents import service as documents
from app.modules.periods.service import grant_override
from app.modules.reports import service as reports
from app.modules.audit.service import events
from app.modules.agent import service as agent
from app.modules.exports.service import create_export

router = APIRouter(prefix='/api/v1')


@router.get('/me')
def me(actor=Depends(current_user)):
    return actor


@router.get('/periods')
def periods(request: Request, actor=Depends(current_user)):
    with request.app.state.db.transaction() as tx:
        return [p for p in tx.all('periods') if p['team_id'] == actor['team_id']
                and (actor['role'] == 'team_lead' or actor['id'] in p['participants'])]


@router.post('/periods/{identity}/deadline-overrides')
def override(identity: str, body: Override, request: Request, actor=Depends(current_user)):
    return grant_override(request.app.state.db, actor, identity, body.model_dump(mode='json'))


@router.get('/documents')
def document_list(request: Request, actor=Depends(current_user)):
    return documents.list_documents(request.app.state.db, actor)


@router.post('/documents', status_code=201)
def document_create(body: NewDocument, request: Request, actor=Depends(current_user)):
    return documents.create_document(request.app.state.db, actor, body.model_dump())


@router.get('/documents/{identity}')
def document_get(identity: str, request: Request, actor=Depends(current_user)):
    return documents.get_document(request.app.state.db, actor, identity)


@router.patch('/documents/{identity}')
def document_save(identity: str, body: SaveDocument, request: Request, actor=Depends(current_user)):
    current = documents.get_document(request.app.state.db, actor, identity)
    if body.kind != current['kind'] or body.period_id != current['period_id']:
        raise DomainError('IMMUTABLE_ASSIGNMENT', 'Không đổi loại hoặc đợt của hồ sơ.', 422)
    return documents.save_document(request.app.state.db, actor, identity, body.model_dump())


@router.get('/documents/{identity}/checks')
def checks(identity: str, request: Request, actor=Depends(current_user)):
    return {'findings': rule_checks(documents.get_document(request.app.state.db, actor, identity)),
            'ai_review_status': 'not_implemented',
            'notice': 'Đây là kiểm tra quy tắc mẫu, chưa phải đánh giá chuyên môn đầy đủ.'}


@router.post('/documents/{identity}/submit')
def submit(identity: str, body: Revision, request: Request, actor=Depends(current_user)):
    return documents.submit(request.app.state.db, actor, identity, body.expected_revision)


@router.post('/documents/{identity}/decisions')
def decision(identity: str, body: Decision, request: Request, actor=Depends(current_user)):
    return documents.decide(request.app.state.db, actor, identity, body.model_dump())


@router.post('/documents/{identity}/revisions', status_code=201)
def revise(identity: str, body: Revision, request: Request, actor=Depends(current_user)):
    return documents.revise(request.app.state.db, actor, identity, body.expected_revision)


@router.post('/documents/{identity}/exports')
def export(identity: str, body: Revision, request: Request, actor=Depends(current_user)):
    return create_export(request.app.state.db, request.app.state.storage, actor, identity, body.expected_revision)


@router.get('/documents/{identity}/file')
def download(identity: str, request: Request, actor=Depends(current_user)):
    doc = documents.get_document(request.app.state.db, actor, identity)
    if not doc.get('export'):
        raise DomainError('NOT_FOUND', 'Chưa có bản xuất.', 404)
    return FileResponse(request.app.state.storage.path(doc['export']['file_key']),
                        filename=f'Edumate-{doc["id"][:8]}-v{doc["version_no"]}.docx',
                        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@router.post('/periods/{identity}/reports', status_code=201)
def report_submit(identity: str, body: TeacherReport, request: Request, actor=Depends(current_user)):
    return reports.submit_report(request.app.state.db, actor, identity, body.model_dump())


@router.post('/periods/{identity}/aggregates', status_code=201)
def aggregate(identity: str, request: Request, actor=Depends(current_user)):
    return reports.aggregate(request.app.state.db, actor, identity)


@router.get('/audit-events')
def audit(request: Request, object_id: str | None = None, actor=Depends(current_user)):
    return events(request.app.state.db, actor, object_id)


@router.post('/agent/drafts')
async def draft(body: DraftRequest, request: Request, actor=Depends(current_user)):
    return await agent.draft(request.app.state.db, request.app.state.provider, actor, body.model_dump())
