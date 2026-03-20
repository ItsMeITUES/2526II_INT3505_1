# RAML 1.0 — Library Management API

## Giới thiệu

**RAML (RESTful API Modeling Language)** là ngôn ngữ mô tả API dựa trên YAML, được phát triển bởi MuleSoft. Điểm mạnh lớn nhất là hỗ trợ **tái sử dụng** (traits, resourceTypes, libraries) giúp tránh lặp code trong các API lớn.

### Ưu điểm
- ✅ **Traits & ResourceTypes**: Tái sử dụng behavior (vd: pagination, authentication) cho nhiều endpoints
- ✅ **Libraries**: Chia sẻ type definitions giữa nhiều API files
- ✅ Cú pháp YAML rõ ràng, có cấu trúc tốt
- ✅ Hỗ trợ type system mạnh (kế thừa, union types)
- ✅ Tích hợp tốt với MuleSoft Anypoint Platform
- ✅ API Console — UI docs đẹp với live testing

### Nhược điểm
- ❌ Chủ yếu gắn với ecosystem của MuleSoft
- ❌ Hệ sinh thái tool ít hơn OpenAPI
- ❌ Cộng đồng nhỏ hơn
- ❌ Ít được update (RAML 2.0 vẫn chưa ra)

---

## Cài đặt & Chạy

### Yêu cầu
- Node.js >= 14
- Java 8+ (cho một số tools)

### 1. Validate RAML với raml-cli

```bash
# Cài raml-cli
npm install -g raml-cli

# Validate file RAML
raml-cli validate library-api.raml
```

### 2. Xem tài liệu với API Console

```bash
# Cài api-console
npm install -g api-console-cli

# Build và serve API Console
api-console build -t library-api.raml

# Hoặc dùng api-console-cli serve (nhanh hơn)
api-console serve -t library-api.raml
# Mở: http://localhost:3000
```

### 3. Convert RAML → OpenAPI (để dùng openapi-generator)

```bash
# Cài oas-raml-converter
npm install -g oas-raml-converter

# Convert RAML → OpenAPI 3.0
oas-raml-converter --from RAML --to OAS30 library-api.raml > library-api.yaml

# Verify kết quả
npx @redocly/cli lint library-api.yaml
```

### 4. Mock server với osprey

```bash
# Cài osprey mock
npm install -g osprey-mock-service

# Chạy mock server
osprey-mock-service -f library-api.raml -p 3000 --cors

# Test
curl http://localhost:3000/api/v1/books
curl -H "Authorization: Bearer token123" http://localhost:3000/api/v1/books
```

### 5. Generate code với RAML to JAX-RS

```bash
# Cài raml-for-jax-rs (Maven)
# Thêm vào pom.xml:
# <dependency>
#   <groupId>org.raml.jaxrs</groupId>
#   <artifactId>raml-to-jaxrs</artifactId>
# </dependency>

# Hoặc dùng MuleSoft Anypoint Studio để generate code
```

### 6. Test với Abao

```bash
# Cài abao
npm install -g abao

# Chạy API tests dựa trên RAML
abao library-api.raml --server http://localhost:3000/api/v1

# Với reporter chi tiết
abao library-api.raml --server http://localhost:3000/api/v1 --reporter spec
```

---

## Tính năng RAML nổi bật trong file này

### Traits (Tái sử dụng behavior)
```yaml
traits:
  paginated:      # Áp dụng query params page, limit cho mọi GET list
  searchable:     # Áp dụng query param search
  secured:        # Áp dụng JWT auth + 401 response
```

### ResourceTypes (Pattern CRUD)
```yaml
resourceTypes:
  collection:     # Pattern cho danh sách: GET (list) + POST (create)
  item:           # Pattern cho item: GET + PUT + DELETE
```

### Type System
```yaml
types:
  Category:       # Enum type tái sử dụng
  Book:           # Complex object type
  CreateBook:     # Derived type (subset of Book)
```

## Cấu trúc file

```
raml/
├── library-api.raml    # RAML spec chính
├── README.md           # File này
└── generated/          # Code generated (gitignore)
```

## Công cụ liên quan

| Công cụ | Mục đích | Link |
|---------|----------|------|
| API Console | Interactive docs | https://api-console.io |
| Anypoint Studio | MuleSoft IDE | https://www.mulesoft.com |
| osprey | Node.js middleware | https://github.com/mulesoft/osprey |
| abao | API testing | https://github.com/cybertk/abao |
| oas-raml-converter | Convert formats | https://github.com/mulesoft/oas-raml-converter |
