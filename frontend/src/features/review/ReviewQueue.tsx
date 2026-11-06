import { useState } from 'react';
import { request, downloadDocument } from '../../lib/api';
import type { Period, SchoolDocument, User } from '../../lib/types';

export function ReviewQueue({ user, documents, periods, refresh, notify }: {
  user: User; documents: SchoolDocument[]; periods: Period[]; refresh: () => Promise<void>; notify: (text: string) => void;
}) {
  const [reason, setReason] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [teacher, setTeacher] = useState('teacher-1');
  const [until, setUntil] = useState('');
  const [extensionReason, setExtensionReason] = useState('Bổ sung theo góp ý chuyên môn');
  if (user.role !== 'team_lead') return <div className="card"><h2>Hàng đợi phê duyệt</h2><p>Chức năng này dành cho tổ trưởng. Giáo viên xem kết quả trong hồ sơ của mình.</p></div>;
  const action = async (work: () => Promise<void>) => { setBusy(true); try { await work(); await refresh(); } catch (e) { notify((e as Error).message); } finally { setBusy(false); } };
  const pending = documents.filter(d => d.status === 'submitted');
  return <div className="stack">
    <div className="card"><h2>Hàng đợi phê duyệt</h2><p className="muted">Kiểm tra bản Word trước khi quyết định. Hồ sơ do chính bạn soạn cần người duyệt thay.</p>
      {!pending.length && <p>Chưa có hồ sơ chờ duyệt.</p>}
      {pending.map(doc => <article className="review-item" key={doc.id}>
        <div className="row spread"><div><h3>{doc.title}</h3><p>{doc.owner_name} · v{doc.version_no} · revision {doc.revision}</p></div><button disabled={busy || !doc.export} onClick={() => action(() => downloadDocument(user.id, doc.id))}>Mở bản Word</button></div>
        <label>Nhận xét / lý do<textarea value={reason[doc.id] || ''} onChange={e => setReason(v => ({ ...v, [doc.id]: e.target.value }))} placeholder="Ghi căn cứ duyệt hoặc phần cần sửa…" /></label>
        <div className="row"><button className="primary" disabled={busy || !reason[doc.id]?.trim() || doc.owner_id === user.id} onClick={() => action(async () => {
          await request(user.id, `/documents/${doc.id}/decisions`, 'POST', { decision: 'approve', reason: reason[doc.id], expected_revision: doc.revision }); notify('Đã duyệt đúng phiên bản.');
        })}>Duyệt phiên bản này</button><button disabled={busy || !reason[doc.id]?.trim() || doc.owner_id === user.id} onClick={() => action(async () => {
          await request(user.id, `/documents/${doc.id}/decisions`, 'POST', { decision: 'request_changes', reason: reason[doc.id], expected_revision: doc.revision }); notify('Đã yêu cầu sửa. Nếu quá hạn, cần cấp cửa sổ sửa.');
        })}>Yêu cầu sửa</button></div>
      </article>)}
    </div>
    <div className="card"><h3>Mở cửa sổ sửa theo người</h3><p className="muted">Đây là ngoại lệ theo thời gian. Bản đã duyệt vẫn bất biến.</p>
      <div className="row wrap"><label>Người được gia hạn<select value={teacher} onChange={e => setTeacher(e.target.value)}>{periods[0]?.participants.map(id => <option key={id} value={id}>{id}</option>)}</select></label>
        <label>Cho phép đến<input type="datetime-local" value={until} onChange={e => setUntil(e.target.value)} /></label></div>
      <label>Lý do<input value={extensionReason} onChange={e => setExtensionReason(e.target.value)} /></label>
      <button disabled={busy || !until || !extensionReason.trim() || !periods.length} onClick={() => action(async () => {
        await request(user.id, `/periods/${periods[0].id}/deadline-overrides`, 'POST', { user_id: teacher, allowed_until: new Date(until).toISOString(), reason: extensionReason, expected_revision: periods[0].revision }); notify('Đã lưu cửa sổ sửa và nhật ký.');
      })}>Cấp thời hạn mới</button>
    </div>
  </div>;
}
