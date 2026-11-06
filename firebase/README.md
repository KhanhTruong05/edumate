# Firebase — cấu hình mẫu, chưa triển khai

Không có project thật, khóa dịch vụ hoặc thao tác deploy trong bộ khung. App demo hiện chạy SQLite/local storage. `firebase.json` và rules là điểm bắt đầu cho giai đoạn nối cloud.

Rules mặc định từ chối client truy cập Firestore/Storage, phù hợp hướng backend-only. Không mở `allow read, write: if true` để làm demo. Firebase Admin SDK bỏ qua Rules; xác minh token, membership, quyền và thời hạn trong backend.

Các bước cần làm: cài requirements-firebase; cấu hình ADC; implement repository Firestore + Cloud Storage; thêm Firebase frontend login; thay demo header bằng Bearer token; chạy lại toàn bộ test với emulator trước khi dùng project thật. Emulator là môi trường kiểm thử, không có nghĩa hiện starter đã nối vào emulator.

Cloud Storage/Cloud Run có yêu cầu billing riêng; đọc giá và cấu hình trước khi tự triển khai. Bộ khung chưa deploy lên Firebase Hosting hoặc Google Cloud.
