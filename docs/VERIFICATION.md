# Kết quả kiểm tra bộ khung

## Tách cổng và bỏ token AI — 12/11/2026

- Backend: **36 test đạt**; AI: **19 test đạt**. Bao gồm gọi AI không có token, lỗi thiếu Gemini key, citation/audit và truy cập demo trực tiếp qua Docker gateway khi được bật.
- Compose publish riêng trên localhost: frontend `8080`, backend `8000`, AI `8001`; dev Vite cố định `5173`. Backend dev mặc định gọi AI qua HTTP tại `127.0.0.1:8001`.
- `docker compose config --quiet` và `git diff --check` đạt. Cả ba image build thành công; TypeScript/Vite build đạt, vẫn có cảnh báo bundle Tiptap/use-client.
- HTTP smoke test: frontend và API qua Nginx, Swagger/health/API trực tiếp ở backend, AI health đều trả 200. Gọi `/drafts` không gửi token trả `503 AI_NOT_CONFIGURED` khi chưa có Gemini key. Không gọi Gemini thật.
- Cảnh báo deprecation Starlette TestClient/httpx vẫn còn. Các mục bên dưới là lịch sử kiểm tra trước thay đổi này.

## Docker ba service — 12/11/2026

- Mỗi phần có `frontend/Dockerfile`, `backend/Dockerfile`, `ai/Dockerfile`; Compose nhận đúng ba service. Root Dockerfile/supervisor của image gộp được bỏ.
- **35 test backend và 21 test AI đạt** trên host. Có test xuyên backend → AI HTTP qua ASGI transport: giữ nguồn theo quyền, citation đúng/sai, audit và yêu cầu người xem xét.
- **Cả ba image build thành công**. Compose chạy thử với project riêng `edumate-three-service-check` tại localhost:18080; cả ba container healthy. Frontend TypeScript/Vite build trong Docker thành công; `nginx -t` đạt.
- Smoke test HTTP qua Nginx đạt: React/assets, docs/OpenAPI, health, chọn danh tính, tạo tài liệu, xuất/tải DOCX, nộp/duyệt và chặn giáo viên khác tải tài liệu.
- Backend → AI container trả đúng `503 AI_NOT_CONFIGURED` khi thiếu Gemini key và ghi audit failed. AI từ chối request thiếu token. Không gọi Gemini thật.
- Dừng riêng AI: backend health và API thủ công vẫn hoạt động. Tạo lại riêng backend: Nginx kết nối lại và hồ sơ đã duyệt trong volume vẫn còn.
- Chạy lại cả hai suite trong backend container Python 3.11 với requirements-lock.txt: **56 test đạt**, xác nhận dependency đã chốt và AI package sau sửa cuối.
- Review độc lập phát hiện cap 6000 source blocks của service không khớp input từ nhiều document hợp lệ. Đã tái hiện RED rồi sửa theo tổng budget 45000 ký tự; test 6003 blocks hợp lệ đạt, tổng ký tự vượt budget bị từ chối.
- Vẫn có cảnh báo deprecation TestClient/httpx từ Starlette. Firebase/Gemini thật, tải lớn và triển khai production chưa được kiểm tra.

## Refactor ba phần — 12/11/2026

- Code AI chuyển sang package độc lập `ai/src/edumate_ai`; backend giữ quyền lấy nguồn, run/audit và chuyển lỗi về API cũ. Frontend không đổi API.
- **24 test backend đạt**: 20 test workflow hiện có và 4 test lỗi upstream qua package thật, adapter và audit.
- **13 test AI đạt**, gồm payload/schema Gemini, lỗi cấu hình/upstream và citation. Test dùng HTTP transport giả lập, không gọi Gemini thật.
- Review độc lập xác nhận ranh giới package và phân quyền được giữ nguyên. Đã sửa thêm lỗi có sẵn khi Gemini trả envelope sai kiểu (`candidates: null` hoặc `parts: [null]`): test AI và API/audit tái hiện lỗi trước sửa, sau sửa trả `AI_UPSTREAM_ERROR` và lưu run thất bại.
- Build wheel `edumate_ai-0.1.0-py3-none-any.whl` thành công; cài vào virtualenv riêng, không có backend, và chạy lại 13 test bằng `python -I` đạt.
- `docker compose -p edumate-refactor-check config --quiet` đạt. Docker Engine có kết nối trong lượt này, nhưng build dừng khi tải image Node do Docker Hub TLS handshake timeout. **Chưa xác nhận image hoặc container runtime sau refactor**.
- Frontend chưa build lại được: Corepack không tải được pnpm từ npm registry do timeout. Mã ứng dụng frontend không đổi; không coi kết quả build cũ là kiểm chứng mới.
- Môi trường: Linux, Python 3.13.14, Node 24.18.1. Cài dependency từ `backend/requirements.txt` cho lần test này; FastAPI 0.162.5, Pydantic 2.14.3, httpx 0.28.1. Thử cài lại đúng lockfile qua `requirements-dev.txt` bị timeout ở PyPI/colorama, nên chưa xác nhận đủ phiên bản đã chốt trên môi trường này.
- Backend có một cảnh báo deprecation từ Starlette TestClient/httpx, không có assertion lỗi. Firebase/Gemini thật chưa được gọi; database vẫn là SQLite.

Lệnh tái hiện sau khi cài từ repository root bằng `python -m pip install -r requirements-dev.txt`:

```sh
cd backend
../.venv/bin/python -m pytest
cd ../ai
../.venv/bin/python -m pytest
```

## Kiểm tra starter trước refactor

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
