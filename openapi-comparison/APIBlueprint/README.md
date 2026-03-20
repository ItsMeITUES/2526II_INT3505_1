# API Blueprint — Library Management API

## Giới thiệu

**API Blueprint** là ngôn ngữ mô tả API dựa trên Markdown, được phát triển bởi Apiary (thuộc Oracle). Đặc điểm nổi bật là cú pháp rất gần với văn bản thường, dễ đọc cho cả developer và non-developer.

### Ưu điểm
- ✅ Cú pháp Markdown thuần túy — rất dễ viết và đọc
- ✅ Tài liệu có thể đọc trực tiếp không cần render
- ✅ Tích hợp tốt với Apiary platform
- ✅ Dễ học cho người mới bắt đầu

### Nhược điểm
- ❌ Hệ sinh thái tool ít hơn OpenAPI nhiều
- ❌ Ít được maintain hơn (phát triển chậm)
- ❌ Không hỗ trợ JSON Schema đầy đủ
- ❌ Code generation hạn chế

---

## Cài đặt & Chạy

### Yêu cầu
- Node.js >= 14
- Ruby (cho Aglio)

### 1. Render tài liệu HTML với Aglio

```bash
# Cài aglio
npm install -g aglio

# Render ra HTML
aglio -i library-api.apib -o library-api.html

# Mở với live reload
aglio -i library-api.apib -s
# Truy cập: http://localhost:3000
```

### 2. Render với theme tùy chỉnh

```bash
# Theme olio (mặc định)
aglio -i library-api.apib -o docs.html --theme-template triple

# Theme slate
aglio -i library-api.apib --theme-variables slate -o docs-slate.html

# Theme flatly
aglio -i library-api.apib --theme-variables flatly -o docs-flatly.html
```

### 3. Parse và validate với drakov

```bash
# Cài drakov (mock server)
npm install -g drakov

# Chạy mock server
drakov -f library-api.apib -p 3000

# Test API
curl http://localhost:3000/books
curl -X POST http://localhost:3000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","author":"Author","isbn":"9780132350884","category":"technology","totalCopies":2}'
```

### 4. Parse với snowcrash (parser chính thức)

```bash
# Cài snowcrash (C++ parser)
# macOS
brew install apiaryio/formulae/apiaryio

# Parse và validate
snowcrash library-api.apib
```

### 5. Convert sang OpenAPI

```bash
# Cài apib2swagger
npm install -g apib2swagger

# Convert
apib2swagger -i library-api.apib -o library-api.yaml

# Sau đó dùng openapi-generator để gen code
```

### 6. Test với Dredd

```bash
# Cài dredd
npm install -g dredd

# Tạo config
dredd init

# Chạy test (cần server đang chạy)
dredd library-api.apib http://localhost:3000/api/v1
```

---

## Cấu trúc file .apib

```
FORMAT: 1A          ← Phiên bản format
HOST: ...           ← Base URL

# Tên API          ← Tiêu đề = tên API

# Group Tên nhóm   ← Nhóm endpoints

## Resource [/path] ← Resource với URL

### Action [METHOD] ← HTTP action

+ Parameters       ← Query/path params
+ Request          ← Request body
+ Response CODE    ← Response
```

## Công cụ liên quan

| Công cụ | Mục đích | Link |
|---------|----------|------|
| Apiary | Hosted docs + mock | https://apiary.io |
| Aglio | HTML render | https://github.com/danielgtaylor/aglio |
| Drakov | Mock server | https://github.com/Aconex/drakov |
| Dredd | API testing | https://github.com/apiaryio/dredd |
| apib2swagger | Convert sang OpenAPI | npm: apib2swagger |
