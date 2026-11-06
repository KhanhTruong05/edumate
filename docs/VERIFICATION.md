# Kết quả kiểm tra bộ khung

Ngày: 06/11/2026. Chạy trên Windows, Python 3.11.9 và Node 24.22.1. Dependency backend được chốt trong requirements-lock.txt; frontend trong pnpm-lock.yaml.

## Đã chạy

- **20 kiểm thử backend đạt** trong `backend/tests/test_workflow.py`.
- **TypeScript kiểm tra kiểu đạt**, Vite build thành công.
- **Kiểm thử trình duyệt đạt:** tạo nháp → xuất DOCX → nộp → đổi vai trò → duyệt → xem audit.
- **Luồng báo cáo qua UI đạt:** một giáo viên nộp 10 nhiệm vụ/8 hoàn thành, tổ trưởng tổng hợp nhận đúng 1/20 người và 80%.
- **Giao diện 390 px:** không tràn ngang trang ở màn hình báo cáo.
- Tệp Word kiểm thử mở được như ZIP DOCX và chứa nội dung mong đợi. Chưa có vòng render/kiểm tra tài liệu theo mẫu trường thật.

Kiểm thử phát hiện và đã sửa lỗi editor tự đánh dấu chưa lưu khi đổi trạng thái editable; sau sửa đã chạy lại luồng trên trình duyệt thành công.

## Các giới hạn của kết quả này

- Chưa gọi Firebase/Gemini thật, chưa deploy dịch vụ cloud, chưa kiểm tra SDK Firebase với project hoặc emulator thật.
- Chưa dùng thử với giáo viên thật, chưa kiểm tra nhiều người dùng đồng thời hoặc tải lớn.
- Provider giả chỉ xuất hiện trong test kiểm chứng citation; UI không có nút sinh AI giả.
- Build hiện có cảnh báo kích thước bundle Tiptap và directive “use client”; không có lỗi biên dịch. Có thể tách tải editor sau khi chốt phạm vi.
- TestClient hiện có cảnh báo deprecation từ thư viện; toàn bộ assertions vẫn đạt. Khi nâng framework cần kiểm tra lại lớp test transport.

Các kết quả trên xác nhận các luồng starter đã kiểm tra, không chứng minh hoàn thành toàn bộ pipeline mở rộng hoặc loại bỏ hallucination.

## Bổ sung đóng gói Docker

- Có Dockerfile nhiều stage, Compose, Nginx reverse proxy, supervisor và healthcheck.
- Compose chỉ publish `127.0.0.1:8080` mặc định; một named volume cho database và tài liệu.
- `docker compose config --quiet` đạt.
- Docker CLI có sẵn nhưng Linux Engine không kết nối được. Thử khởi động Desktop báo `context deadline exceeded`; chưa xác định nguyên nhân ở WSL/thiết lập ứng dụng.
- **Chưa build image hoặc chạy container**; chưa xác nhận permission volume/non-root, Nginx hoặc healthcheck trong runtime Linux. Không ghi các phần này là đã đạt.
- Đường API Docker được build thành `/api/v1`; link Swagger được đổi theo API base để dùng được cả local dev và cùng cổng qua proxy.
