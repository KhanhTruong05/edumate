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

`backend/requirements.txt` và `requirements-lock.txt` liệt kê dependency bên ngoài. Lệnh cài ở root trong `requirements-dev.txt` cài cả dependency backend và package AI local. Khi đóng gói riêng backend, cần gửi/cài cả package `ai/`; `backend/Dockerfile` đã làm việc này với build context là repository root.

## Ranh giới với AI

`modules/agent/tools.py` kiểm tra quyền và lấy nguồn. `modules/agent/service.py` ghi run/audit, gọi provider và kiểm tra citation bằng `edumate_ai`. `modules/agent/provider.py` chuyển `AIError` thành `DomainError`. Phần gọi Gemini, prompt và schema nằm trong `ai/`.

Frontend tiếp tục gọi `POST /api/v1/agent/drafts`. Backend không tự áp bản AI, không trao quyền database hoặc duyệt cho package AI.

## Kiểm thử

```sh
cd backend
python -m pytest
```

Chạy sau khi đã cài dependency và AI package theo lệnh ở root. Test không cần Firebase hoặc Gemini thật.

## Docker và AI HTTP

```sh
# Từ repository root
docker build -f backend/Dockerfile -t edumate-backend .
```

Dev mặc định gọi `http://127.0.0.1:8001`; Compose đặt `AI_SERVICE_URL=http://ai:8001`, không cần token giữa backend và AI; backend dùng `modules/agent/remote.py` để gọi HTTP, validate schema rồi kiểm tra citation. Gemini key cấu hình ở service AI (`ai/.env` khi dev). Chạy AI ở terminal riêng theo README gốc. Provider local vẫn có thể dùng bằng cách chủ động để trống URL và cấu hình Gemini tại backend.

Backend vẫn cài package `edumate_ai` cho schema/citation và provider local; ba image chưa hoàn toàn độc lập về mã dùng chung. `/health` trả `ai_configured: null` khi dùng remote provider vì key/model ở service AI; xem `/health` của AI trong container để biết trạng thái cấu hình model.

Backend lắng nghe `0.0.0.0:8000` trong container, Compose publish `127.0.0.1:8000:8000`. Compose bật `DEMO_ALLOW_DIRECT_ACCESS=true` để request từ host qua Docker gateway dùng được bộ chọn danh tính demo. Chỉ bật tùy chọn này khi cổng được giới hạn ở localhost. Mặc định ngoài Compose, backend vẫn chỉ nhận loopback hoặc proxy có `DEMO_PROXY_TOKEN`. Đây vẫn là danh tính demo, không thay thế Firebase Auth.
