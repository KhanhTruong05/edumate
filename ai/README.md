# EduMate AI

Package Python `edumate_ai` quản lý Gemini provider, prompt sinh nháp, schema đầu ra và đối chiếu citation. Lõi package không đọc database hoặc biến môi trường, không phụ thuộc FastAPI/backend. HTTP entry point tùy chọn (`service.py`) đọc cấu hình và dùng FastAPI; package không phụ thuộc backend và không có quyền nộp/duyệt tài liệu.

## Cài và kiểm thử độc lập

Cần Python 3.11+. Từ thư mục gốc repository, dùng Python trong virtualenv:

```sh
python -m pip install -e "./ai[service]" pytest
cd ai
python -m pytest
```

Không cần chạy backend hoặc có Gemini key để chạy test. Các test gọi provider thật qua HTTP transport giả lập; không gọi dịch vụ bên ngoài.

## Sử dụng

```python
from edumate_ai import AIError, GeminiProvider, verify_claims

provider = GeminiProvider(key=api_key, model=model_id)
# sources phải do bên gọi kiểm tra quyền trước khi truyền vào.
result = await provider.draft(kind="lesson", instructions="Soạn bài theo nguồn", sources=sources)
errors = verify_claims(result["claims"], sources)
```

`sources` là danh sách dict với `id` và `text`, có thể kèm metadata. Đầu ra có `sections` (title/text), `claims` (text/source_id/quote), `warnings`. `AIError` có `code`, `message`, `status`; backend chuyển lỗi này thành lỗi API và ghi audit. `configured` cho biết key/model đã được cung cấp hợp lệ về hình thức.

Khi dev, Gemini key/model được đặt trong `ai/.env` và nạp bằng `uvicorn --env-file ai/.env`. Với Docker, Compose chỉ truyền khóa Gemini vào container `ai`, backend gọi HTTP không cần token. Citation khớp chưa bảo đảm nội dung đúng; đầu ra luôn cần người xem xét.

Code chính nằm ở `src/edumate_ai/`: `provider.py` gọi model và chứa prompt, `schemas.py` quy định đầu ra, `quality.py` kiểm tra citation, `errors.py` quy định lỗi độc lập.

## Chạy thành service riêng

`ai/Dockerfile` đóng gói HTTP service tại port 8001; build context là repository root. Compose truyền Gemini key/model vào container và publish `127.0.0.1:8001:8001` ra host.

```sh
# Từ repository root
docker build -f ai/Dockerfile -t edumate-ai .
```

Chạy trực tiếp ngoài Docker sau khi cài extra `service`:

```sh
cp ai/.env.example ai/.env  # Chỉ lần đầu; điền Gemini key/model nếu cần.
python -m uvicorn edumate_ai.service:create_app --factory --env-file ai/.env --host 127.0.0.1 --port 8001
```

`GET /health` kiểm tra service và trả `ai_configured`; thiếu Gemini key không làm service unhealthy. `POST /drafts` không yêu cầu token, nhận body `{kind,instructions,sources}`. Lỗi `{code,message}` giữ hợp đồng AI cũ. Backend kiểm tra quyền nguồn trước khi gọi và kiểm tra citation trước khi lưu kết quả.
