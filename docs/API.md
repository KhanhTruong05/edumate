# API chính

Chạy backend và mở `/docs` để xem schema thực tế. Trong demo dùng header `X-Demo-User: teacher-1` hoặc `lead-1` trên kết nối cục bộ.

| Method | Route sau `/api/v1` | Mục đích |
|---|---|---|
| GET | /me | Danh tính demo hiện tại |
| GET | /periods | Các kỳ thuộc quyền |
| POST | /periods/{id}/deadline-overrides | Cửa sổ sửa cho một người, cần expected_revision của kỳ |
| GET/POST | /documents | Danh sách / tạo nháp |
| GET/PATCH | /documents/{id} | Đọc / lưu nháp với expected_revision |
| GET | /documents/{id}/checks | Kiểm tra quy tắc mẫu |
| POST | /documents/{id}/exports | Tạo bản Word gắn với content_hash |
| GET | /documents/{id}/file | Tải bản xuất qua kiểm tra quyền |
| POST | /documents/{id}/submit | Chốt trạng thái nộp, cần bản Word hiện hành |
| POST | /documents/{id}/decisions | approve hoặc request_changes; cần lý do |
| POST | /documents/{id}/revisions | Tạo bản mới từ bản đã duyệt/cần sửa |
| POST | /periods/{id}/reports | Nộp báo cáo định lượng bất biến |
| POST | /periods/{id}/aggregates | Chốt nguồn và tính số liệu |
| GET | /audit-events | Nhật ký; tùy chọn object_id |
| POST | /agent/drafts | Lấy nguồn, gọi Gemini và kiểm chứng nháp |

Lỗi domain trả `{code,message}`. `403`: sai quyền; `404`: không có dữ liệu hoặc ngoài phạm vi đọc; `409`: revision/trạng thái; `423`: quá hạn; `422`: dữ liệu; `503 AI_NOT_CONFIGURED`: thiếu cấu hình AI. Lỗi Pydantic có cấu trúc `detail` mặc định của FastAPI.

Endpoint export dùng python-docx và một mẫu cố định, không gọi dịch vụ conversion trả phí. Không có endpoint ký hoặc tự chuyển hồ sơ lên trường trong starter.
