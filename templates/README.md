# Mẫu tài liệu

Starter hiện dựng một mẫu DOCX bằng `backend/app/modules/exports/service.py`: A4, Times New Roman 13pt, lề cố định, các mục từ editor và bảng cơ bản. Chưa lấy mẫu thật của trường.

Để mở rộng, thêm thư mục `lesson/`, `plan/`, `report/` với DOCX do đơn vị xác nhận, version và bộ trường đầu vào. Có thể dùng docxtpl để điền đúng mẫu. Phải kiểm tra font, lề, bảng dài, ngắt trang và đầu/cuối trang bằng Word hoặc công cụ render trước khi phát hành. Không chỉ dựa vào việc file mở được.
