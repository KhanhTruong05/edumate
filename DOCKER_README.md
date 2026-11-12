# EduMate — Chạy ba service bằng Docker

Repository dùng mô hình **monorepo nhiều service**: mỗi phần có image/container riêng, Compose kết nối và khởi động chúng cùng nhau.

```text
Trình duyệt → localhost:8080 → frontend (React + Nginx)
                                 ↓ HTTP nội bộ
                              backend (FastAPI + SQLite/file)
                                 ↓ HTTP nội bộ, có token
                              ai (FastAPI + Gemini)
```

Backend vẫn là ứng dụng nghiệp vụ dạng module và dùng chung package schema/citation với AI. Tách Docker không tự động biến toàn bộ nghiệp vụ thành kiến trúc microservices hoàn chỉnh.

## Chạy toàn bộ

Cần Docker Engine/Desktop với Linux containers, Compose và internet lần build đầu. Từ repository root:

```sh
docker compose up --build -d
docker compose ps
```

Mở **http://localhost:8080**. Swagger tại **http://localhost:8080/docs**, backend health tại **http://localhost:8080/health**. Chưa cần Gemini key để dùng soạn thảo, Word, nộp, duyệt và báo cáo.

Chỉ frontend publish port trên `127.0.0.1`. Backend 8000 và AI 8001 dùng mạng Docker, không publish ra host. Frontend chờ backend healthy; backend không chờ AI để các chức năng thủ công vẫn sử dụng được khi AI ngừng chạy.

## Ba Dockerfile

| Phần | Dockerfile | Runtime |
|---|---|---|
| Frontend | `frontend/Dockerfile` | Build React bằng Node, phục vụ qua Nginx |
| Backend | `backend/Dockerfile` | FastAPI, một worker, chạy UID 10001, volume `/data` |
| AI | `ai/Dockerfile` | FastAPI AI service, chạy UID 10001, không mount database |

**Build context của cả ba là repository root**, không phải từng thư mục. Backend vẫn cần package `ai/` cho schema/citation và local provider.

```sh
docker build -f frontend/Dockerfile -t edumate-frontend .
docker build -f backend/Dockerfile -t edumate-backend .
docker build -f ai/Dockerfile -t edumate-ai .
```

Thông thường chỉ cần Compose; nó tự chọn đúng Dockerfile. Build/chạy lại một phần:

```sh
docker compose up -d --build --no-deps ai
docker compose up -d --build --no-deps backend
docker compose up -d --build --no-deps frontend
```

Nginx resolve lại Docker DNS để tiếp tục kết nối khi backend được tạo lại. Khi đổi schema/protocol dùng chung, cần kiểm tra và rebuild cả backend lẫn AI.

## Cấu hình Gemini và cổng

Sao chép `.env.example` ở root thành `.env` nếu chưa có, rồi điền:

```dotenv
EDUMATE_PORT=8080
GEMINI_API_KEY=khóa_của_bạn
GEMINI_MODEL=ID_model_được_cấp_quyền
```

Compose chỉ truyền Gemini key/model vào **container ai**. Sau khi đổi cấu hình:

```sh
docker compose up -d ai
```

Không cần build lại chỉ để đổi key. Đổi `EDUMATE_PORT=8090` rồi `docker compose up -d frontend` nếu cổng 8080 bận. Docker không đọc `backend/.env`; file đó dành cho dev local.

`AI_SERVICE_TOKEN` xác thực backend → AI. `DEMO_PROXY_TOKEN` xác thực Nginx → backend cho bộ chọn tài khoản demo. Compose có giá trị mẫu để chạy ngay trên localhost; các giá trị này không phải đăng nhập production. Nếu thay token, dùng chuỗi chữ/số/dấu gạch và cập nhật các service liên quan bằng `docker compose up -d`. Nginx ghi đè header token từ trình duyệt; backend không tin forwarded-IP headers.

## Dữ liệu, log và dừng

```sh
docker compose logs --tail=80 frontend backend ai
docker compose stop
docker compose start
# Gỡ container/network nhưng giữ database và file:
docker compose down
```

Volume `edumate_data` giữ nguyên tên khai báo từ bản image gộp trước, giờ được mount vào backend. Giữ cùng tên project Compose/thư mục để tiếp tục dùng dữ liệu cũ; không thêm tùy chọn xóa volume nếu muốn giữ hồ sơ.

Healthcheck AI chỉ kiểm tra service có chạy; thiếu key vẫn healthy và sinh nháp trả `AI_NOT_CONFIGURED`. Health backend không phụ thuộc AI; khi dùng remote provider, `ai_configured` là `null` vì backend không giữ key/model. Xem cấu hình AI bằng:

```sh
docker compose exec ai python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8001/health').read().decode())"
```

Bản này vẫn dùng SQLite và danh tính demo, chưa nối Firebase thật. Xem `docs/VERIFICATION.md` cho kết quả kiểm tra build/runtime mới nhất.
