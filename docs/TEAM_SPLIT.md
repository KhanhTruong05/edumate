# Hai người tiếp tục phát triển

| Người | Module / thư mục sở hữu | Việc tiếp theo |
|---|---|---|
| A | core, domain/policies, auth, periods, documents, audit, Firebase repository | Nối auth thật, Firestore transaction, thu hồi override, idempotency, quản trị kỳ và quyền |
| B | agent, exports, reports, frontend editor, templates | Chạy thử Gemini thật, provenance run/version, import DOCX, mẫu docxtpl, hoàn thiện báo cáo tổ |

Mỗi người làm cả UI và API cho phần mình. Chốt API schema khi đổi; chạy kiểm thử quyền, hạn, revision và số liệu khi thay repository. Không bỏ cơ chế chặn self-approval hoặc tự áp nội dung AI khi tích hợp cloud.

Bộ khung này là điểm bắt đầu; phạm vi soạn mới/editor/import/ký đã rộng hơn bản 10 ngày trước đó. Ước lượng lại trên các đầu việc còn thiếu trong README thay vì coi starter là hoàn thành toàn bộ kế hoạch.
