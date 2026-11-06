const base = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1';
export const apiDocsUrl = /^https?:\/\//i.test(base) ? new URL('/docs', base).href : '/docs';

export async function request<T>(identity: string, path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    method, headers: { 'Content-Type': 'application/json', 'X-Demo-User': identity },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message = data.message || (Array.isArray(data.detail) ? data.detail.map((d: { msg: string }) => d.msg).join('; ') : data.detail);
    throw new Error(message || `Lỗi ${response.status}`);
  }
  return response.json();
}

export async function downloadDocument(identity: string, id: string): Promise<void> {
  const response = await fetch(`${base}/documents/${id}/file`, { headers: { 'X-Demo-User': identity } });
  if (!response.ok) throw new Error('Không tải được tài liệu hoặc không có quyền.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url; link.download = `EduMate-${id.slice(0, 8)}.docx`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
