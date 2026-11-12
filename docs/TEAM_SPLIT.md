# Phân chia theo frontend, backend và AI

| Phần | Module / thư mục sở hữu | Việc tiếp theo |
|---|---|---|
| Frontend | `frontend/` | Giao diện đăng nhập, editor, quản trị kỳ, báo cáo và duyệt theo API |
| Backend | `backend/`, `firebase/`, `templates/` | Nối auth thật, Firestore transaction, quyền, audit, exports, reports và cấp nguồn cho AI |
| AI | `ai/` | Chạy thử Gemini thật, cải thiện prompt/schema/citation và chất lượng sinh nháp |

Đây là ba phần code, không bắt buộc ba người hoặc ba service. Nếu có hai người, có thể phân một người backend, người còn lại frontend và AI. Chốt API schema khi đổi; chạy kiểm thử quyền, hạn, revision và số liệu khi thay repository. Không bỏ cơ chế chặn self-approval hoặc tự áp nội dung AI khi tích hợp cloud.

Hợp đồng AI là `draft(kind, instructions, sources)` trả sections/claims/warnings và `verify_claims(claims, sources)` trả lỗi citation. Quyền lấy nguồn, run/version và audit do backend sở hữu; AI không truy cập database. Cấu hình Firebase chưa trở thành database thật trong lần refactor này.

Bộ khung này là điểm bắt đầu; phạm vi soạn mới/editor/import/ký đã rộng hơn bản 10 ngày trước đó. Ước lượng lại trên các đầu việc còn thiếu trong README thay vì coi starter là hoàn thành toàn bộ kế hoạch.
