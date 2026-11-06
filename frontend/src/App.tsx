import { useCallback, useEffect, useState } from 'react';
import { request, apiDocsUrl } from './lib/api';
import type { AuditEvent, Period, SchoolDocument, User } from './lib/types';
import { Workspace } from './features/authoring/Workspace';
import { ReviewQueue } from './features/review/ReviewQueue';
import { Reports } from './features/reports/Reports';
import { AuditLog } from './features/audit/AuditLog';

const tabs = [['overview', 'Tổng quan'], ['authoring', 'Soạn thảo'], ['review', 'Duyệt & gia hạn'], ['reports', 'Báo cáo'], ['audit', 'Nhật ký']] as const;
type Page = typeof tabs[number][0];

export default function App() {
  const [identity, setIdentity] = useState('teacher-1');
  const [page, setPage] = useState<Page>('overview');
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<SchoolDocument[]>([]);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const refresh = useCallback(async () => {
    const [me, docs, rounds, logs] = await Promise.all([
      request<User>(identity, '/me'), request<SchoolDocument[]>(identity, '/documents'),
      request<Period[]>(identity, '/periods'), request<AuditEvent[]>(identity, '/audit-events'),
    ]);
    setUser(me); setDocuments(docs); setPeriods(rounds); setEvents(logs); setError('');
  }, [identity]);
  useEffect(() => { setUser(null); refresh().catch(e => setError((e as Error).message)); }, [refresh]);
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span>E</span>EduMate</div><p className="muted small">Workspace · Starter 0.1</p>
      <nav aria-label="Chức năng">{tabs.map(([id, title]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { if (page === 'authoring' && !confirm('Chuyển trang có thể mất phần chưa lưu. Tiếp tục?')) return; setPage(id); setNotice(''); }}>{title}</button>)}</nav>
      <div className="sidebar-bottom"><strong>Local demo</strong><p>SQLite + lưu tệp cục bộ. Chưa nối Firestore/Storage cho các route này.</p><a href={apiDocsUrl} target="_blank" rel="noreferrer">Xem API Swagger ↗</a></div>
    </aside>
    <main>
      <header className="topbar"><div><span className="eyebrow">TỔ CHUYÊN MÔN · DỮ LIỆU GIẢ LẬP</span><h1>{tabs.find(([id]) => id === page)?.[1]}</h1></div>
        <label className="identity-label">Tài khoản demo<select aria-label="Tài khoản demo" value={identity} onChange={e => { if (!confirm('Đổi tài khoản sẽ đóng phần đang soạn. Tiếp tục?')) return; setIdentity(e.target.value); setPage('overview'); setNotice(''); }}>
          <option value="teacher-1">Giáo viên 1</option><option value="teacher-2">Giáo viên 2</option><option value="lead-1">Tổ trưởng</option><option value="lead-2">Người duyệt thay</option>
        </select></label>
      </header>
      <div className="demo-banner">Bộ khung chạy thử trên máy cá nhân. Chưa phải bản dùng thật cho nhà trường; lựa chọn tài khoản demo không phải đăng nhập Firebase.</div>
      {notice && <div className="notice" role="status">{notice}<button aria-label="Đóng thông báo" onClick={() => setNotice('')}>×</button></div>}
      {error ? <div className="card error" role="alert"><h2>Chưa kết nối backend</h2><p>{error}</p><p>Kiểm tra ứng dụng đang chạy theo README hoặc xem log Docker, rồi thử lại.</p><button onClick={() => refresh().catch(e => setError((e as Error).message))}>Thử lại</button></div> : !user ? <p>Đang tải dữ liệu…</p> : <>
        {page === 'overview' && <>
          <section className="hero"><span className="eyebrow">XIN CHÀO, {user.name.toUpperCase()}</span><h2>Soạn rõ ràng.<br/>Duyệt đúng phiên bản.</h2><p>Tạo tài liệu, kiểm tra thời hạn, xem bản Word và theo dõi lịch sử. Các thay đổi được lưu ở backend.</p><button onClick={() => setPage('authoring')}>Bắt đầu soạn tài liệu →</button></section>
          <div className="metrics card">{[['Tài liệu / phiên bản', documents.length], ['Chờ duyệt', documents.filter(d => d.status === 'submitted').length], ['Đã duyệt', documents.filter(d => d.status === 'approved').length], ['Cần sửa', documents.filter(d => d.status === 'changes_requested').length]].map(([label, count]) => <div key={label}><strong>{count}</strong><span>{label}</span></div>)}</div>
          <div className="columns"><article className="card"><h3>Đợt đang dùng thử</h3><p>{periods[0]?.name}</p><p>Hạn: {periods[0] && new Date(periods[0].due_at).toLocaleString('vi-VN')}</p><p className="muted">Khóa được kiểm tra bằng giờ máy chủ ở mỗi lần ghi/nộp. Tổ trưởng có thể mở cửa sổ sửa.</p></article><article className="card"><h3>AI có kiểm chứng</h3><p>Agent có bước lấy nguồn, gọi Gemini và kiểm tra trích dẫn.</p><p className="muted">Cần khóa API để sinh nội dung. Nguồn dẫn đúng chưa bảo đảm suy luận đúng; bản AI luôn cần người xem xét.</p></article></div>
        </>}
        {page === 'authoring' && <Workspace key={identity} user={user} documents={documents} periods={periods} refresh={refresh} notify={setNotice} />}
        {page === 'review' && <ReviewQueue user={user} documents={documents} periods={periods} refresh={refresh} notify={setNotice} />}
        {page === 'reports' && <Reports key={identity} user={user} periods={periods} refresh={refresh} notify={setNotice} />}
        {page === 'audit' && <AuditLog events={events} />}
      </>}
      <footer>EduMate starter · Không tự ký hoặc tự duyệt bằng AI · Xem README để biết phạm vi đã có và chưa có.</footer>
    </main>
  </div>;
}
