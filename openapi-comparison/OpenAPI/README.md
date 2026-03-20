# OpenAPI 3.1 — Library Management API

## Giới thiệu

**OpenAPI Specification (OAS)** là tiêu chuẩn mô tả REST API phổ biến nhất hiện nay, được duy trì bởi OpenAPI Initiative (Linux Foundation). Phiên bản 3.1 tích hợp đầy đủ với JSON Schema Draft 2020-12.

### Ưu điểm
- ✅ Hệ sinh thái tool phong phú nhất (Swagger, Redoc, Stoplight...)
- ✅ Hỗ trợ generate code cho 50+ ngôn ngữ (openapi-generator)
- ✅ Tích hợp với nhiều API gateway (Kong, AWS API GW, Azure APIM)
- ✅ Cú pháp YAML/JSON quen thuộc
- ✅ Validation schema mạnh (JSON Schema)

### Nhược điểm
- ❌ Verbose cho API phức tạp
- ❌ Không mô tả được async/event-driven API (dùng AsyncAPI thay thế)

---

## Cài đặt & Chạy

### Yêu cầu
- Node.js >= 18
- npm hoặc npx

### 1. Xem tài liệu với Swagger UI

```bash
# Dùng npx (không cần cài toàn cục)
npx @redocly/cli preview-docs library-api.yaml

# Hoặc dùng Swagger UI qua Docker
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/api/library-api.yaml \
  -v $(pwd):/api \
  swaggerapi/swagger-ui

# Mở trình duyệt: http://localhost:8080
```

### 2. Validate spec

```bash
npx @redocly/cli lint library-api.yaml
```

### 3. Generate code từ spec

```bash
# Cài openapi-generator-cli
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript client
openapi-generator-cli generate \
  -i library-api.yaml \
  -g typescript-axios \
  -o ./generated/typescript-client

# Generate Python client
openapi-generator-cli generate \
  -i library-api.yaml \
  -g python \
  -o ./generated/python-client

# Generate Node.js Express server stub
openapi-generator-cli generate \
  -i library-api.yaml \
  -g nodejs-express-server \
  -o ./generated/express-server
```

### 4. Generate tests với Schemathesis

```bash
pip install schemathesis

# Chạy fuzz testing dựa trên spec
schemathesis run library-api.yaml --base-url http://localhost:3000/api/v1

# Với report
schemathesis run library-api.yaml \
  --base-url http://localhost:3000/api/v1 \
  --report report.html
```

### 5. Mock server

```bash
# Prism mock server
npx @stoplight/prism-cli mock library-api.yaml

# Mở terminal khác, test:
curl http://127.0.0.1:4010/api/v1/books
curl -X POST http://127.0.0.1:4010/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","author":"Author","isbn":"9780132350884","category":"technology","totalCopies":2}'
```

---

## Cấu trúc file

```
openapi/
├── library-api.yaml          # Spec chính (OpenAPI 3.1)
├── README.md                 # File này
└── generated/                # Code được generate (gitignore)
    ├── typescript-client/
    ├── python-client/
    └── express-server/
```

## Công cụ liên quan

| Công cụ | Mục đích | Link |
|---------|----------|------|
| Swagger Editor | Edit online | https://editor.swagger.io |
| Redocly | Lint + docs | https://redocly.com |
| Stoplight | Design-first | https://stoplight.io |
| Prism | Mock server | https://stoplight.io/prism |
| openapi-generator | Code gen | https://openapi-generator.tech |