import { useState } from 'react';
import type { JSONContent } from '@tiptap/react';
import { DocumentEditor } from '../../components/DocumentEditor';
import { request, downloadDocument } from '../../lib/api';
import { kindLabels, statusLabels } from '../../lib/types';
import type { AgentRun, DocumentKind, Period, SchoolDocument, User } from '../../lib/types';

const initialContent: JSONContent = { type: 'doc', content: [
  { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Mục tiêu' }] },
  { type: 'paragraph', content: [{ type: 'text', text: 'Nhập mục tiêu bài học và thông tin thực tế tại đây.' }] },
  { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Hoạt động dạy học' }] },
  { type: 'paragraph', content: [{ type: 'text', text: 'Mô tả hoạt động của giáo viên và học sinh.' }] },
  { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Đánh giá' }] },
  { type: 'paragraph', content: [{ type: 'text', text: 'Bổ sung cách đánh giá phù hợp với mục tiêu.' }] },
] };

export function Workspace({ user, periods, documents, refresh, notify }: {
  user: User; periods: Period[]; documents: SchoolDocument[]; refresh: () => Promise<void>; notify: (s: string) => void;
}) {
  const [doc, setDoc] = useState<SchoolDocument | null>(null);
  const [title, setTitle] = useState('Giáo án mới');
  const [kind, setKind] = useState<DocumentKind>('lesson');
  const [content, setContent] = useState<JSONContent>(initialContent);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [generation, setGeneration] = useState(0);
  const [prompt, setPrompt] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [findings, setFindings] = useState<string[]>([]);
  const writable = !busy && (!doc || (doc.status === 'draft' && doc.owner_id === user.id));

  const useDocument = (value: SchoolDocument | null) => {
    if (dirty && !confirm('Có nội dung chưa lưu. Bạn muốn bỏ thay đổi để mở tài liệu khác?')) return;
    setDoc(value); setTitle(value?.title || 'Giáo án mới'); setKind(value?.kind || 'lesson');
    setContent(value?.content || initialContent); setDirty(false); setGeneration(v => v + 1); setRun(null); setFindings([]);
  };
  const action = async (work: () => Promise<void>) => {
    setBusy(true);
    try { await work(); await refresh(); } catch (error) { notify((error as Error).message); }
    finally { setBusy(false); }
  };
  const save = async () => {
    const body = { title, kind, period_id: doc?.period_id || periods[0]?.id, content };
    const saved = doc
      ? await request<SchoolDocument>(user.id, `/documents/${doc.id}`, 'PATCH', { ...body, expected_revision: doc.revision })
      : await request<SchoolDocument>(user.id, '/documents', 'POST', body);
    setDoc(saved); setDirty(false); notify('Đã lưu bản nháp và ghi nhật ký.');
    return saved;
  };

  return <div className="workspace">
    <aside className="document-list card">
      <button className="primary full" onClick={() => useDocument(null)} disabled={busy}>+ Tài liệu mới</button>
      <h3>Hồ sơ trong phạm vi quyền</h3>
      {!documents.length && <p className="muted">Chưa có tài liệu. Hãy tạo bản nháp đầu tiên.</p>}
      {documents.map(item => <button className={`document-item ${doc?.id === item.id ? 'selected' : ''}`} key={item.id} onClick={() => useDocument(item)} disabled={busy}>
        <strong>{item.title}</strong><span>{item.owner_name} · v{item.version_no}</span><span>{statusLabels[item.status]}</span>
      </button>)}
    </aside>
    <section className="writing-area">
      <div className="card">
        <div className="row spread"><h2>{doc ? 'Chi tiết tài liệu' : 'Soạn tài liệu mới'}</h2><span className="badge">{doc ? statusLabels[doc.status] : 'Chưa lưu'}</span></div>
        <label>Tên tài liệu<input value={title} disabled={!writable} onChange={e => { setTitle(e.target.value); setDirty(true); }} /></label>
        <div className="row"><label>Loại tài liệu<select value={kind} disabled={!writable || !!doc} onChange={e => { setKind(e.target.value as DocumentKind); setDirty(true); }}>
          {Object.entries(kindLabels).map(([value, text]) => <option key={value} value={value}>{text}</option>)}
        </select></label><p className="muted">{doc ? `Phiên bản ${doc.version_no} · Revision ${doc.revision}` : periods[0]?.name}</p></div>
        {doc?.review_note && <div className="note">Góp ý: {doc.review_note}</div>}
        <DocumentEditor content={content} valueKey={`${doc?.id || 'new'}:${generation}`} editable={writable} onChange={value => { setContent(value); setDirty(true); }} />
        <p className="muted small">{dirty ? 'Có thay đổi chưa lưu.' : 'Nội dung đang khớp bản đã mở/lưu.'} Bố cục web không bảo đảm giống Word; mở DOCX để kiểm tra.</p>
        <div className="row wrap">
          <button className="primary" disabled={!writable || !periods.length} onClick={() => action(async () => { await save(); })}>Lưu bản nháp</button>
          <button disabled={busy || !writable} onClick={() => action(async () => {
            const saved = dirty || !doc ? await save() : doc;
            const exported = await request<SchoolDocument>(user.id, `/documents/${saved.id}/exports`, 'POST', { expected_revision: saved.revision });
            setDoc(exported); await downloadDocument(user.id, exported.id); notify('Đã tạo DOCX. Mở file kiểm tra trước khi nộp.');
          })}>Tạo bản Word để kiểm tra</button>
          <button disabled={busy || !doc?.export || dirty || doc.status !== 'draft' || doc.owner_id !== user.id} onClick={() => action(async () => {
            if (!doc) return;
            const saved = await request<SchoolDocument>(user.id, `/documents/${doc.id}/submit`, 'POST', { expected_revision: doc.revision });
            setDoc(saved); notify('Đã nộp, phiên bản được khóa.');
          })}>Xác nhận đã xem Word & nộp</button>
          {doc?.export && <button disabled={busy} onClick={() => action(() => downloadDocument(user.id, doc.id))}>Tải bản đã xuất</button>}
          {doc && ['approved', 'changes_requested'].includes(doc.status) && doc.owner_id === user.id && <button disabled={busy} onClick={() => action(async () => {
            const value = await request<SchoolDocument>(user.id, `/documents/${doc.id}/revisions`, 'POST', { expected_revision: doc.revision }); useDocument(value);
          })}>Tạo phiên bản sửa</button>}
          {doc && <button disabled={busy || dirty} onClick={() => action(async () => {
            const result = await request<{ findings: { message: string }[]; notice: string }>(user.id, `/documents/${doc.id}/checks`);
            setFindings([result.notice, ...result.findings.map(f => f.message)]);
          })}>Kiểm tra quy tắc mẫu</button>}
        </div>
        {!!findings.length && <ul className="note">{findings.map((f, i) => <li key={i}>{f}</li>)}</ul>}
      </div>
      <div className="card ai-panel">
        <div className="row spread"><h3>Trợ lý soạn nháp</h3><span className="badge">Gemini · cần cấu hình</span></div>
        <p className="muted">Chỉ gọi khi bạn bấm nút. Không tự lưu nội dung, không tự duyệt. Nếu thiếu khóa API sẽ báo rõ.</p>
        <label>Yêu cầu<textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ví dụ: soạn mục hoạt động ôn tập cho bài… dựa trên nguồn đã chọn." /></label>
        {!!documents.length && <details><summary>Chọn tài liệu nguồn được phép xem</summary>{documents.slice(0, 8).map(d => <label className="checkbox" key={d.id}>
          <input type="checkbox" checked={sources.includes(d.id)} onChange={e => setSources(v => e.target.checked ? [...v, d.id] : v.filter(id => id !== d.id))} />{d.title} · {statusLabels[d.status]}
        </label>)}</details>}
        <button disabled={!writable || prompt.trim().length < 10} onClick={() => action(async () => {
          setRun(await request<AgentRun>(user.id, '/agent/drafts', 'POST', { kind, instructions: prompt, source_ids: sources }));
        })}>Đề xuất bản nháp bằng AI</button>
        {run && <div className="note"><strong>{run.status}</strong><p>{run.notice}</p>
          {run.validation_errors.map((e, i) => <p key={i}>{e.message}</p>)}
          {run.result && <><ul>{run.result.sections.map((section, i) => <li key={i}><b>{section.title}</b>: {section.text}</li>)}</ul>
            {run.result.warnings.map((w, i) => <p key={i}>{w}</p>)}
            <details><summary>Nguồn của nhận xét</summary><pre>{JSON.stringify(run.result.claims, null, 2)}</pre></details>
            <button disabled={!writable} onClick={() => {
              if (!confirm('Áp dụng nháp AI sẽ thay nội dung đang soạn. Bạn đã kiểm tra các đề xuất?')) return;
              setContent({ type: 'doc', content: run.result!.sections.flatMap(section => [
                { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: section.title }] },
                { type: 'paragraph', content: [{ type: 'text', text: section.text }] },
              ]) }); setGeneration(v => v + 1); setDirty(true);
            }}>Chấp nhận vào editor — chưa lưu</button></>}
        </div>}
      </div>
    </section>
  </div>;
}
