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

Compose đặt `AI_SERVICE_URL=http://ai:8001` và `AI_SERVICE_TOKEN`; backend dùng `modules/agent/remote.py` để gọi HTTP, validate schema rồi kiểm tra citation. Gemini key không truyền backend trong Compose. Bỏ trống URL để giữ provider local khi chạy dev.

Backend vẫn cài package `edumate_ai` cho schema/citation và provider local; ba image chưa hoàn toàn độc lập về mã dùng chung. `/health` trả `ai_configured: null` khi dùng remote provider vì key/model ở service AI; xem `/health` của AI trong container để biết trạng thái cấu hình model.

Backend lắng nghe `0.0.0.0:8000` trong container và không publish ra host. Nginx truyền `X-Edumate-Proxy-Token`; backend chỉ chấp nhận kết nối từ container khi token khớp `DEMO_PROXY_TOKEN`. Dev loopback vẫn dùng bộ chọn tài khoản như trước. Đây vẫn là danh tính demo, không thay thế Firebase Auth.
