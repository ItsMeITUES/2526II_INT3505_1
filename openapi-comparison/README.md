# API Documentation Format Comparison

So sánh 4 format tài liệu hóa REST API phổ biến thông qua demo ứng dụng **Quản lý Thư viện**.

---

## Tổng quan so sánh

| Tiêu chí | OpenAPI 3.1 | API Blueprint | RAML 1.0 | TypeSpec |
|---|---|---|---|---|
| **Cú pháp** | YAML/JSON | Markdown | YAML | TypeScript-like |
| **Độ phổ biến** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ (đang tăng) |
| **Code generation** | Xuất sắc (50+ ngôn ngữ) | Hạn chế | Tốt (qua convert) | Tốt (qua OpenAPI output) |
| **Mock server** | Prism | Drakov | Osprey | Prism (qua OpenAPI) |
| **Validation** | JSON Schema đầy đủ | Cơ bản | Type system riêng | TypeScript-like |
| **Tái sử dụng** | $ref, components | Tài liệu cơ bản | Traits, ResourceTypes | Generics, Decorators |
| **IDE support** | Tốt | Cơ bản | Tốt | Xuất sắc (VS Code) |
| **Learning curve** | Trung bình | Thấp | Trung bình | Cao |
| **Ecosystem** | Lớn nhất | Nhỏ | Trung bình | Đang phát triển |
| **Maintained by** | OpenAPI Initiative | Apiary/Oracle | MuleSoft | Microsoft |

---

## Cấu trúc thư mục

```
openapi-comparison/
├── README.md                    ← File này
│
├── openapi/                     ← OpenAPI 3.1
│   ├── library-api.yaml         ← Spec chính
│   └── README.md                ← Hướng dẫn cài đặt & chạy
│
├── api-blueprint/               ← API Blueprint
│   ├── library-api.apib         ← Spec chính
│   └── README.md
│
├── raml/                        ← RAML 1.0
│   ├── library-api.raml         ← Spec chính
│   └── README.md
│
└── typspec/                     ← TypeSpec (Microsoft)
    ├── library-api.tsp          ← Source TypeSpec
    ├── tspconfig.yaml           ← Config output
    ├── package.json
    └── README.md
```

---

## API được document: Library Management

Tất cả 4 format đều mô tả cùng một API với các tính năng:

| Resource | Endpoints |
|----------|-----------|
| **Books** | `GET /books` · `POST /books` · `GET /books/:id` · `PUT /books/:id` · `DELETE /books/:id` |
| **Members** | `GET /members` · `POST /members` · `GET /members/:id` · `GET /members/:id/loans` |
| **Loans** | `GET /loans` · `POST /loans` · `GET /loans/:id` · `POST /loans/:id/return` |

---

## Khi nào dùng format nào?

### Dùng OpenAPI khi:
- Cần hệ sinh thái tool lớn nhất
- Cần code generation cho nhiều ngôn ngữ
- Tích hợp với API gateway (Kong, AWS, Azure APIM)
- Team cần standard rõ ràng được industry công nhận

### Dùng API Blueprint khi:
- Team gồm cả non-developer (PM, designer)
- Ưu tiên tài liệu đọc được như văn bản thường
- Dùng Apiary platform
- API nhỏ, đơn giản

### Dùng RAML khi:
- Dùng MuleSoft Anypoint Platform
- API lớn, cần tái sử dụng nhiều (traits, resourceTypes)
- Cần định nghĩa type system phức tạp

### Dùng TypeSpec khi:
- Team quen với TypeScript
- Cần generate nhiều format khác nhau từ một source
- Xây dựng API trong Azure ecosystem
- Muốn type-safe API design với IDE support mạnh

---

## Demo: Code & Test Generation từ API Docs

Xem thư mục `codegen-demo/` để xem demo sinh code và test từ các file tài liệu.

```bash
# Quick start với OpenAPI (được hỗ trợ tốt nhất)
cd openapi
npx @stoplight/prism-cli mock library-api.yaml
# → Mock server chạy tại http://localhost:4010

# Test ngay:
curl http://localhost:4010/books
```
