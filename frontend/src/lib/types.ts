import type { JSONContent } from '@tiptap/react';

export type User = { id: string; name: string; role: 'teacher' | 'team_lead'; team_id: string };
export type Period = { id: string; name: string; due_at: string; revision: number; participants: string[]; overrides: Record<string, { allowed_until: string }>; closed: boolean };
export type DocumentKind = 'lesson' | 'plan' | 'personal_report';
export type SchoolDocument = {
  id: string; title: string; kind: DocumentKind; period_id: string; content: JSONContent;
  owner_id: string; owner_name: string; status: 'draft' | 'submitted' | 'approved' | 'changes_requested';
  revision: number; version_no: number; content_hash: string; parent_id: string | null;
  export: { file_key: string; content_hash: string } | null; review_note?: string;
};
export type AuditEvent = { id: string; actor_name: string; action: string; object_id: string; occurred_at: string; before: unknown; after: unknown; reason: string };
export type AgentRun = { status: string; notice: string; validation_errors: { message: string }[]; result?: { sections: { title: string; text: string }[]; claims: { text: string; source_id: string; quote: string }[]; warnings: string[] } };
export const kindLabels: Record<DocumentKind, string> = { lesson: 'Giáo án', plan: 'Kế hoạch giảng dạy', personal_report: 'Báo cáo cá nhân' };
export const statusLabels: Record<SchoolDocument['status'], string> = { draft: 'Bản nháp', submitted: 'Chờ duyệt', approved: 'Đã duyệt', changes_requested: 'Cần chỉnh sửa' };
