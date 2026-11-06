import { useState } from 'react';
import { request } from '../../lib/api';
import type { Period, User } from '../../lib/types';

type Aggregate = { id: string; source_ids: string[]; submitted_count: number; expected_count: number; missing_user_ids: string[]; metrics: { assigned: number; completed: number; completion_rate: number | null; eligible_count: number; unique_activity_count: number }; note: string };

export function Reports({ user, periods, refresh, notify }: { user: User; periods: Period[]; refresh: () => Promise<void>; notify: (s: string) => void }) {
  const [assigned, setAssigned] = useState('');
  const [completed, setCompleted] = useState('');
  const [achievements, setAchievements] = useState('');
  const [difficulties, setDifficulties] = useState('');
  const [activity, setActivity] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState<Aggregate | null>(null);
  const period = periods[0];
  const action = async (work: () => Promise<void>) => { setBusy(true); try { await work(); await refresh(); } catch (e) { notify((e as Error).message); } finally { setBusy(false); } };
  return <div className="stack">
    {user.role === 'teacher' && <div className="card"><h2>Báo cáo định lượng cá nhân</h2><p className="muted">Số liệu do người dùng xác nhận. Hai trường trống nghĩa là không áp dụng; số 0 được giữ nguyên.</p>
      <div className="row wrap"><label>Nhiệm vụ được giao<input type="number" min="0" value={assigned} onChange={e => setAssigned(e.target.value)} /></label><label>Đã hoàn thành<input type="number" min="0" value={completed} onChange={e => setCompleted(e.target.value)} /></label></div>
      <div className="row wrap">{[['A1', 'Sinh hoạt tổ'], ['A2', 'Dự giờ chung'], ['A3', 'Chuyên đề chung']].map(([code, name]) => <label key={code} className="checkbox"><input type="checkbox" checked={activity.includes(code)} onChange={e => setActivity(v => e.target.checked ? [...v, code] : v.filter(x => x !== code))} />{name}</label>)}</div>
      <label>Kết quả thực hiện<textarea value={achievements} onChange={e => setAchievements(e.target.value)} /></label>
      <label>Khó khăn<textarea value={difficulties} onChange={e => setDifficulties(e.target.value)} /></label>
      <button className="primary" disabled={busy || !period} onClick={() => action(async () => {
        await request(user.id, `/periods/${period.id}/reports`, 'POST', { assigned: assigned === '' ? null : Number(assigned), completed: completed === '' ? null : Number(completed), activity_codes: activity, achievements, difficulties, proposals: '' }); notify('Đã nộp báo cáo mới; bản cũ được giữ lịch sử.');
      })}>Nộp báo cáo</button>
    </div>}
    {user.role === 'team_lead' && <div className="card"><h2>Tổng hợp từ nguồn đã nộp</h2><p className="muted">Chốt một phiên bản mỗi người. Chức năng starter hiện có số liệu và nguồn; chưa soạn/duyệt/xuất báo cáo tổ.</p>
      <button disabled={busy || !period} onClick={() => action(async () => { setSummary(await request<Aggregate>(user.id, `/periods/${period.id}/aggregates`, 'POST')); })}>Chốt nguồn và tính số liệu</button>
      {summary && <><h3>{summary.submitted_count}/{summary.expected_count} người đã nộp</h3><div className="metrics"><div><strong>{summary.metrics.assigned}</strong><span>Được giao</span></div><div><strong>{summary.metrics.completed}</strong><span>Hoàn thành</span></div><div><strong>{summary.metrics.completion_rate === null ? 'N/A' : `${(summary.metrics.completion_rate * 100).toFixed(1)}%`}</strong><span>Tỷ lệ cùng tập nguồn hợp lệ</span></div></div>
        <p>Hoạt động chung không trùng: {summary.metrics.unique_activity_count}. Có số liệu áp dụng: {summary.metrics.eligible_count} người.</p><p className="note">{summary.note}</p><details><summary>Nguồn và người chưa nộp</summary><pre>{JSON.stringify({ source_ids: summary.source_ids, missing: summary.missing_user_ids }, null, 2)}</pre></details></>}
    </div>}
  </div>;
}
