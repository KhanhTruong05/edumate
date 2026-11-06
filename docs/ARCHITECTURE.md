# Kiến trúc starter

## Hiện chạy cục bộ

```text
React/Vite + Tiptap
        → FastAPI API schemas / demo identity
        → Domain policies: quyền, hạn, revision, bất biến
        → SQLite transaction + audit
        → LocalStorage: tệp DOCX

Agent: collect_sources theo quyền → Gemini REST → Pydantic → verify_claims
Reports: chọn bản mới nhất mỗi người → tính cùng tập nguồn hợp lệ → lưu snapshot
```

`main.py` là composition root. Route chỉ nhận/validate dữ liệu và gọi service. Các kiểm tra nghiệp vụ dùng lại từ `domain`. Ghi trạng thái và audit trong cùng transaction SQLite; tệp được render ngoài transaction rồi gắn sau khi kiểm tra lại revision. Có thể có tệp mồ côi nếu render xong nhưng gắn thất bại; chưa có job dọn tệp.

## Nối Firebase sau này

1. Tạo interface repository thay cho `Database/Transaction`; implement Firestore theo cùng hợp đồng nghiệp vụ.
2. Xác minh Firebase ID token rồi đọc membership ở server; không tin role do frontend truyền.
3. Giữ kiểm tra quyền, deadline và revision ở backend. Firestore Admin SDK không bị Security Rules giới hạn như client.
4. Dùng Firestore transaction cho state + audit. Không gọi Gemini hoặc tải tệp trong transaction callback có thể được chạy lại.
5. Thay LocalStorage bằng Cloud Storage private; API tải kiểm tra quyền trước khi trả dữ liệu/URL có hạn.
6. Sau khi có test parity, thêm mode Firebase vào composition root; hiện khởi động mode cloud bị chặn.

`infrastructure/firebase_gateway.py` chỉ chứa nền tảng SDK, chưa thực hiện repository và chưa kiểm thử với project thật. Rules hiện mặc định deny client writes/reads; mọi truy cập thật phải đi qua backend có quyền phù hợp.

## Ranh giới kiểm chứng AI

Đầu ra Gemini có sections/claims/warnings. Quote phải xuất hiện trong nguồn được cấp với ID chứa document + revision + block. Sai nguồn thì không trả kết quả vào editor; quote đúng vẫn mang trạng thái `needs_human_review`.

Các kiểm tra này chưa tự chứng minh mọi câu trong phần soạn là đúng, chưa phát hiện được hết claim không được mô hình khai báo và chưa xác minh mọi số trong prose. Agent result chưa gắn provenance vào tài liệu sau khi người dùng sửa/apply; cần bổ sung liên kết run/version và policy kiểm chứng lại trước khi dùng thật. Không dùng nhãn “đã kiểm chứng đúng hoàn toàn”.

## Lịch sử

SQLite có trigger chặn UPDATE/DELETE audit qua kết nối ứng dụng. Admin sở hữu file database vẫn có thể thay schema; đây không phải WORM. Audit lưu thay đổi metadata, trạng thái, revision và hash nội dung; chưa lưu diff chi tiết mọi đoạn trong editor. Nháp sửa tăng revision; sau nộp không sửa content tại chỗ. “Tạo bản sửa” tạo document ID mới trỏ parent_id và bỏ quyết định duyệt/export cũ.
