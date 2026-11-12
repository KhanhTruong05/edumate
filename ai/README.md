# EduMate AI

Package Python `edumate_ai` quản lý Gemini provider, prompt sinh nháp, schema đầu ra và đối chiếu citation. Package không đọc database hoặc biến môi trường, không phụ thuộc FastAPI/backend và không có quyền nộp/duyệt tài liệu.

## Cài và kiểm thử độc lập

Cần Python 3.11+. Từ thư mục gốc repository, dùng Python trong virtualenv:

```sh
python -m pip install -e ./ai pytest
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

Backend vẫn đọc `GEMINI_API_KEY`/`GEMINI_MODEL` từ `backend/.env` hoặc môi trường Docker rồi truyền vào package. Không thêm `.env` riêng cho AI khi chạy chung backend. Citation khớp chưa bảo đảm nội dung đúng; đầu ra luôn cần người xem xét.

Code chính nằm ở `src/edumate_ai/`: `provider.py` gọi model và chứa prompt, `schemas.py` quy định đầu ra, `quality.py` kiểm tra citation, `errors.py` quy định lỗi độc lập.
