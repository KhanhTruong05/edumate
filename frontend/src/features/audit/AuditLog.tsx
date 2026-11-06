import type { AuditEvent } from '../../lib/types';

export function AuditLog({ events }: { events: AuditEvent[] }) {
  return <div className="card"><h2>Nhật ký hoạt động</h2><p className="muted">200 sự kiện gần nhất trong phạm vi quyền. Tài khoản ứng dụng không được chỉnh hoặc xóa lịch sử.</p>
    {!events.length && <p>Chưa có sự kiện.</p>}
    <div className="table-scroll"><table><thead><tr><th>Thời điểm</th><th>Người thực hiện</th><th>Thao tác</th><th>Thay đổi</th></tr></thead><tbody>{events.map(event => <tr key={event.id}>
      <td>{new Date(event.occurred_at).toLocaleString('vi-VN')}</td><td>{event.actor_name}</td><td><code>{event.action}</code><div className="small muted">{event.object_id.slice(0, 12)}</div></td>
      <td><details><summary>Trước / sau</summary><pre>{JSON.stringify({ before: event.before, after: event.after, reason: event.reason }, null, 2)}</pre></details></td>
    </tr>)}</tbody></table></div>
  </div>;
}
