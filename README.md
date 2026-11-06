# EduMate — Bộ khung mã nguồn

Cập nhật: 06/11/2026. Đây là starter chạy cục bộ để xem cấu trúc code và tiếp tục phát triển; **chưa phải toàn bộ MVP trong kế hoạch đã hoàn thành**.

## Chạy nhanh bằng Docker

Mở Docker Desktop, chờ Engine sẵn sàng. Tại thư mục này:

```sh
docker compose up --build -d
```

Mở http://localhost:8080. Không cần cài Python/Node riêng, chưa cần key để dùng các luồng thủ công. Xem [hướng dẫn Docker](DOCKER_README.md) để cấu hình AI, đổi cổng và giữ dữ liệu. Bản đóng gói hiện mới kiểm tra Compose/build frontend/backend local; **chưa chạy container được vì Engine trên máy tạo gói không khởi động thành công**.

## 1. Cấu trúc

```text
edumate/
├── frontend/                      # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/            # Toolbar và editor Tiptap
│   │   ├── features/
│   │   │   ├── authoring/         # Giáo án / kế hoạch / báo cáo văn bản
│   │   │   ├── review/            # Duyệt và cửa sổ sửa theo hạn
│   │   │   ├── reports/           # Form số liệu và xem tổng hợp
│   │   │   └── audit/             # Nhật ký trước–sau
│   │   └── lib/                   # API client và kiểu dữ liệu
│   └── .env.example
├── backend/                       # FastAPI, Python
│   ├── app/
│   │   ├── api/                   # Route và schema đầu vào
│   │   ├── core/                  # Cấu hình, thời gian và lỗi
│   │   ├── domain/                # Quyền/hạn/revision, kiểm chứng nguồn
│   │   ├── infrastructure/        # SQLite, tệp local, adapter Firebase
│   │   └── modules/
│   │       ├── auth/              # Danh tính demo
│   │       ├── periods/           # Gia hạn theo người
│   │       ├── documents/         # Soạn/lưu/nộp/sửa/duyệt
│   │       ├── agent/             # Tools, Gemini, kiểm chứng nháp
│   │       ├── reports/           # Báo cáo và tính số liệu
│   │       ├── audit/             # Đọc nhật ký theo quyền
│   │       └── exports/           # Tạo DOCX và gắn đúng phiên bản
│   ├── tests/                     # Kiểm thử nghiệp vụ và API
│   ├── requirements.txt
│   └── .env.example
├── firebase/                      # Rules và cấu hình mẫu, chưa deploy
├── docker/                        # Nginx, supervisor và healthcheck
├── Dockerfile                     # Build frontend và gói runtime
├── compose.yaml                   # Chạy bằng một lệnh, volume dữ liệu
├── templates/                     # Đặc tả mẫu tài liệu
├── scripts/                       # Lệnh chạy backend/frontend
└── docs/                          # Kiến trúc, API, phân công, trạng thái
```

## 2. Chạy thử không dùng Docker

Cần Python 3.11+ và Node.js 22.12+ hoặc 24+. Dùng pnpm 11; có thể dùng npm nếu máy đã có npm đi kèm Node. Mở terminal tại thư mục `edumate`.

### Terminal 1 — backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
Copy-Item backend\.env.example backend\.env
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Sau lần cài đầu, có thể dùng `scripts/Run-Backend.ps1`. Tệp `.env` do bạn tạo; đừng ghi đè nếu đã có cấu hình thật. Máy Linux/macOS dùng `.venv/bin/python` tương ứng.

### Terminal 2 — frontend

```powershell
Set-Location frontend
pnpm install --frozen-lockfile
pnpm dev
```

Nếu dùng npm: `npm install`, `npm run dev`; npm không sử dụng pnpm-lock.yaml. Bản đã kiểm tra sử dụng pnpm; khuyến nghị cùng công cụ để tái hiện dependency.

- Giao diện: http://127.0.0.1:5173
- API Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Không mở trực tiếp `frontend/index.html`: trình duyệt cần Vite để biên dịch TypeScript.

## 3. Tài khoản và dữ liệu demo

Chọn trên thanh đầu trang: Giáo viên 1, Giáo viên 2, Tổ trưởng hoặc Người duyệt thay. Đây là **bộ chọn danh tính demo qua header**, chưa phải đăng nhập Firebase. Backend chỉ nhận danh tính demo từ kết nối loopback; không dùng cơ chế này cho triển khai công khai.

Lần đầu khởi động tạo 20 tài khoản giáo viên, 2 tài khoản duyệt và một đợt có hạn sau 7 ngày. Mẫu số báo cáo chỉ gồm 20 giáo viên. Dữ liệu demo lưu tại `backend/.data`; khởi động lại không mất dữ liệu. Có thể đổi vị trí bằng `EDUMATE_DATA_DIR`. Không dùng dữ liệu học sinh thật trong starter.

## 4. Luồng thử được ngay

1. Chọn Giáo viên 1 → Soạn thảo → nhập tên và nội dung.
2. Dùng toolbar in đậm/nghiêng, tiêu đề, danh sách hoặc bảng; lưu nháp.
3. Bấm Tạo bản Word; mở DOCX kiểm tra rồi xác nhận nộp.
4. Chọn Tổ trưởng → Duyệt & gia hạn → tải Word, ghi nhận xét và duyệt/yêu cầu sửa.
5. Quay lại giáo viên để tạo phiên bản sửa. Bản đã nộp/duyệt giữ nguyên.
6. Vào Nhật ký để xem người, thời điểm, trước–sau của metadata, trạng thái và mã nội dung.
7. Giáo viên điền form Báo cáo; tổ trưởng chốt nguồn và tính tổng. Thử cho hai giáo viên cùng chọn A1 để xem hoạt động chung không bị cộng trùng.

Mặc định mẫu DOCX dùng Times New Roman, khổ A4, lề và bảng cơ bản. Bảng xuất hiện tại chỉ giữ văn bản trong ô; chưa giữ mọi định dạng phong phú của bảng. Bố cục editor web không đồng nhất tuyệt đối với Word.

## 5. Bật Gemini — tùy chọn

Trong `backend/.env`:

```dotenv
GEMINI_API_KEY=đặt_khóa_của_bạn_tại_đây
GEMINI_MODEL=ID_model_tài_khoản_được_cấp_quyền
```

Khởi động lại backend. Không đặt khóa vào `frontend` hoặc biến `VITE_*`. Khi bấm sinh nháp, dữ liệu yêu cầu và nguồn đã chọn được gửi tới Gemini; chọn tài liệu giả lập/đã xử lý thông tin phù hợp để thử.

Thiếu cấu hình sẽ trả `AI_NOT_CONFIGURED`, không sinh nội dung mẫu giả làm AI. Kiểm thử dùng provider giả **chỉ trong test**, không thay thế Gemini trong giao diện. Chưa gọi Gemini thật khi bàn giao vì chưa có key/model người dùng.

Agent hiện là workflow giới hạn: thu nguồn theo quyền → gọi Gemini → validate cấu trúc → đối chiếu trích dẫn → trả bản nháp chờ người xem xét. Không có công cụ ký hoặc duyệt. Quote khớp chưa chứng minh suy luận đúng; chưa có đánh giá chất lượng chuyên môn trên dữ liệu trường. AI chưa tự xử lý lại báo cáo tổ; hiện tổng hợp số liệu bằng mã.

## 6. Trạng thái chức năng

| Chức năng | Trạng thái trong starter |
|---|---|
| React, editor Tiptap cơ bản | Chạy được |
| Tạo, lưu nháp, kiểm tra revision | Chạy được |
| Nộp, duyệt, yêu cầu sửa, tạo phiên bản mới | Chạy được |
| Khóa theo hạn máy chủ, gia hạn từng người | Chạy được; API thu hồi override chưa làm |
| Nhật ký append-only trong SQLite | Chạy được; không ghi từng phím hoặc mọi thay đổi bên trong Word ngoài app |
| Form báo cáo, tổng số liệu, chốt phiên bản nguồn | Chạy được |
| Xuất Word cho tài liệu editor | Chạy được bằng python-docx, một mẫu lập trình cố định |
| Gemini soạn giáo án/kế hoạch/báo cáo văn bản | Có connector; cần cấu hình và kiểm tra với model thật |
| Kiểm chứng citation AI | Có kiểm tra xác định; chưa bảo đảm loại bỏ hallucination hoặc đánh giá entailment |
| Firebase Admin/Auth/Firestore/Storage | Có gateway mẫu; **chưa nối vào route nghiệp vụ** |
| Nhập tài liệu DOCX vào editor | Chưa làm |
| Bộ mẫu trường bằng docxtpl, nhiều mẫu | Chưa làm; mẫu hiện tại dùng python-docx |
| AI rà soát chuyên môn đầy đủ | Chưa làm; `/checks` chỉ là quy tắc mẫu |
| Báo cáo tổ: AI soạn, sửa, duyệt, xuất | Chưa làm; hiện trả số liệu và snapshot nguồn |
| Ký, tải bằng chứng ký, trạng thái chuyển trường | Chưa làm |
| Quản trị nhiều tổ/trường, tạo kỳ từ UI | Chưa làm; dữ liệu seed cố định |
| Job AI bền vững, retry sau crash, idempotency tổng quát | Chưa làm; AI hiện gọi đồng bộ, run được ghi trạng thái |

Các loại “kế hoạch”, “giáo án”, “báo cáo văn bản” dùng chung editor; chưa có bộ quy tắc riêng theo mọi loại tài liệu. Cửa sổ sửa kiểm tra ở mỗi lần ghi; khóa phiên bản đã nộp không thể bị gia hạn để ghi đè. Nộp lặp một bản đã nộp bị từ chối theo trạng thái; các endpoint tạo mới chưa có idempotency key tổng quát.

## 7. Kiểm thử và build

```powershell
# Từ thư mục edumate
Set-Location backend
..\.venv\Scripts\python.exe -m pytest
# Terminal khác, tại frontend
pnpm build
```

Kiểm thử tập trung vào: quyền xem/tải/duyệt, quá hạn, gia hạn, revision cũ, bản duyệt bất biến, không tự duyệt, audit không sửa được, cộng đúng nguồn mới nhất, tỷ lệ có mẫu số đúng, số 0/không áp dụng, thiếu API key và citation giả. Xem `docs/VERIFICATION.md` cho kết quả đã chạy.

## 8. Hướng phát triển tiếp

Đọc `docs/ARCHITECTURE.md`, `docs/TEAM_SPLIT.md` và `firebase/README.md`. Hoàn thành repository cloud + Firebase identity, giữ nguyên kiểm tra domain và test trước khi deploy. `APP_MODE` khác `demo` hiện bị từ chối lúc khởi động để không vô tình đưa demo identity lên cloud.

Tham chiếu chính thức: [Vite](https://vite.dev/guide/), [Tiptap React](https://tiptap.dev/docs/editor/getting-started/install/react), [Firebase Admin](https://firebase.google.com/docs/admin/setup), [Gemini API](https://ai.google.dev/gemini-api/docs).
