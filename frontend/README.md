# EduMate frontend

React + TypeScript + Vite, editor Tiptap. Frontend quản lý giao diện soạn thảo, duyệt, báo cáo và nhật ký; gọi backend qua `src/lib/api.ts`. Mọi yêu cầu AI cũng đi qua backend để kiểm tra quyền và ghi audit.

## Cài và chạy

Cần Node.js 22.12+ hoặc 24+ và pnpm 11. Trong thư mục `frontend`:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

Backend cần chạy tại `http://127.0.0.1:8000`. Có thể đặt `VITE_API_BASE` theo `.env.example`. Không đặt khóa Gemini hay khóa dịch vụ vào biến `VITE_*`.

## Kiểm tra build

```sh
pnpm build
```

Dockerfile gốc build frontend với đường dẫn API `/api/v1` và phục vụ cùng cổng qua Nginx.
