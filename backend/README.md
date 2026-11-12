# EduMate backend

FastAPI sở hữu API, danh tính, phân quyền, thời hạn, tài liệu, duyệt, báo cáo, xuất Word và audit. Hiện dùng SQLite + file local; Firebase gateway mới là mẫu tích hợp.

## Cài và chạy

Từ thư mục gốc repository (Python 3.11+):

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp backend/.env.example backend/.env
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Chỉ sao chép `.env` lần đầu nếu chưa có cấu hình. Windows dùng `.venv\Scripts\Activate.ps1`; xem README gốc và `scripts/Run-Backend.ps1`.

`backend/requirements.txt` và `requirements-lock.txt` liệt kê dependency bên ngoài. Lệnh cài ở root trong `requirements-dev.txt` cài cả dependency backend và package AI local. Khi đóng gói riêng backend, cần gửi/cài cả package `ai/`; Dockerfile gốc đã làm việc này.

## Ranh giới với AI

`modules/agent/tools.py` kiểm tra quyền và lấy nguồn. `modules/agent/service.py` ghi run/audit, gọi provider và kiểm tra citation bằng `edumate_ai`. `modules/agent/provider.py` chuyển `AIError` thành `DomainError`. Phần gọi Gemini, prompt và schema nằm trong `ai/`.

Frontend tiếp tục gọi `POST /api/v1/agent/drafts`. Backend không tự áp bản AI, không trao quyền database hoặc duyệt cho package AI.

## Kiểm thử

```sh
cd backend
python -m pytest
```

Chạy sau khi đã cài dependency và AI package theo lệnh ở root. Test không cần Firebase hoặc Gemini thật.
