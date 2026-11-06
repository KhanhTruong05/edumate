# EduMate — Chạy bằng Docker

Gói demo chạy frontend, FastAPI và Nginx trong một image, truy cập qua một cổng. Không cần cài riêng Python, Node hoặc pnpm trên máy người chạy.

## 1. Điều kiện

- Cài và mở Docker Desktop ở chế độ Linux containers, hoặc dùng Docker Engine Linux cùng Compose plugin.
- Có internet ở lần build đầu để tải image nền và dependency.
- Kiểm tra Engine đã sẵn sàng bằng `docker info` và kiểm tra Compose bằng `docker compose version`.

Nếu gặp `dockerDesktopLinuxEngine ... file specified` hoặc `context deadline exceeded`, Docker CLI chưa kết nối được Linux Engine. Mở Docker Desktop và kiểm tra thông báo tại ứng dụng; nguyên nhân có thể cần kiểm tra WSL/virtualization hoặc hoàn tất thiết lập. Lỗi này xảy ra trước bước build EduMate, chưa xác định được nguyên nhân cụ thể chỉ từ thông báo đó.

## 2. Chạy nhanh

Giải nén gói code. Mở terminal trong thư mục `edumate` chứa `compose.yaml`, rồi chạy:

```sh
docker compose up --build -d
```

Mở:

- Giao diện: http://localhost:8080
- Swagger API: http://localhost:8080/docs
- Health: http://localhost:8080/health

Lần đầu chưa cần tạo `.env`. Chọn Giáo viên 1, Giáo viên 2, Tổ trưởng hoặc Người duyệt thay để chạy các luồng demo. Gemini chưa có key thì báo chưa cấu hình, các thao tác thủ công vẫn dùng được.

Đây vẫn là bản demo cục bộ dùng SQLite và tệp local; chưa nối Firebase thật, chưa có ký/chuyển trường và không phải đăng nhập production. Compose chỉ công bố cổng trên loopback `127.0.0.1` của máy người chạy.

## 3. Xem trạng thái, dừng và chạy lại

```sh
docker compose ps
docker compose logs --tail=80 app
docker compose stop
docker compose start
```

Hoặc gỡ container/network nhưng giữ dữ liệu:

```sh
docker compose down
docker compose up -d
```

Database và DOCX nằm trong named volume `edumate_data` thuộc project Compose. `stop` và `down` thông thường giữ volume. Việc xóa volume sẽ xóa dữ liệu demo đã lưu; không dùng tùy chọn xóa volume nếu muốn giữ hồ sơ. Giữ cùng tên project/thư mục khi chạy lại để dùng đúng volume cũ.

## 4. Cấu hình Gemini — tùy chọn

Sao chép `.env.example` ở thư mục gốc thành `.env`, rồi nhập:

```dotenv
EDUMATE_PORT=8080
GEMINI_API_KEY=khóa_của_bạn
GEMINI_MODEL=ID_model_được_cấp_quyền
```

Áp dụng lại biến môi trường:

```sh
docker compose up -d --force-recreate
```

Không cần build lại khi chỉ đổi key/model. Docker dùng `.env` ở thư mục gốc, không dùng `backend/.env`. Khóa chỉ truyền vào môi trường backend lúc chạy; không đặt vào biến `VITE_*`, không gửi `.env` cho người khác hoặc đưa vào ZIP. Khi gọi AI, nội dung yêu cầu và nguồn đã chọn được gửi tới nhà cung cấp.

## 5. Nếu cổng 8080 đang bận

Tạo `.env` từ mẫu và đổi:

```dotenv
EDUMATE_PORT=8090
```

Chạy `docker compose up -d` và mở http://localhost:8090. Frontend dùng `/api/v1` tương đối nên không cần sửa code hoặc build lại chỉ để đổi cổng host.

## 6. Cấu trúc Docker

```text
Dockerfile                 Node build React → Python runtime + Nginx
compose.yaml               Một service app, volume dữ liệu, publish localhost
.dockerignore              Loại dependency local, cache, dữ liệu và .env khỏi build
docker/nginx.conf          Static React + proxy API/docs/health sang loopback
docker/start.py            Khởi động/giám sát hai tiến trình và nhận tín hiệu dừng
docker/healthcheck.py       Kiểm tra API qua chính Nginx
```

FastAPI chỉ lắng nghe `127.0.0.1:8000` bên trong container. Nginx chuyển tiếp qua loopback thật nên không phải bỏ kiểm tra danh tính demo đang giới hạn kết nối cục bộ. Không publish cổng 8000 riêng ra ngoài. Container chạy UID 10001 và ghi database/file vào `/data` được mount volume.

## 7. Kết quả kiểm tra của bản đóng gói

Xem `docs/VERIFICATION.md`. Cấu hình Compose được kiểm tra bằng `docker compose config --quiet`. Máy tạo gói chưa khởi động được Docker Engine nên **chưa build/chạy image, chưa xác nhận healthcheck và volume trong container thực tế**. Các luồng ứng dụng local đã được kiểm tra riêng; không coi đó là kết quả test Docker.

## 8. Gửi cho bạn cùng nhóm

Gửi ZIP code đã đóng gói, giải nén và chạy lệnh ở mục 2. ZIP không chứa `node_modules`, môi trường ảo, dữ liệu đã chạy, khóa API hoặc image Docker build sẵn. Máy người nhận cần build lần đầu; đây chưa phải gói chạy offline bằng `docker load`.
