# TypeSpec — Library Management API

## Giới thiệu

**TypeSpec** (trước đây là CADL) là ngôn ngữ mô tả API mới nhất, được phát triển bởi **Microsoft**. Cú pháp giống TypeScript, hỗ trợ type system mạnh mẽ và **compile ra nhiều format** (OpenAPI 3.x, JSON Schema, Protobuf, gRPC...).

TypeSpec là hướng tiếp cận "API-first with code" — bạn viết TypeSpec như viết code TypeScript, sau đó compile ra OpenAPI hay bất kỳ format nào.

### Ưu điểm
- ✅ **Type-safe**: Cú pháp TypeScript-like, IDE support tốt (VS Code extension)
- ✅ **Multi-target**: Compile ra OpenAPI, Protobuf, JSON Schema, GraphQL từ một source
- ✅ **Generics**: Hỗ trợ generic types (`PagedResponse<T>`, `ItemResponse<T>`)
- ✅ **Decorators**: Mạnh mẽ tương tự TypeScript decorators
- ✅ **Microsoft ecosystem**: Dùng bởi Azure, đang phát triển nhanh
- ✅ Tái sử dụng model tốt — không cần lặp lại định nghĩa

### Nhược điểm
- ❌ Còn khá mới, ecosystem đang phát triển
- ❌ Learning curve cao hơn YAML-based formats
- ❌ Ít tool hỗ trợ hơn OpenAPI
- ❌ Breaking changes thường xuyên trong các phiên bản sớm

---

## Cài đặt & Chạy

### Yêu cầu
- Node.js >= 18

### 1. Cài đặt dependencies

```bash
cd typspec
npm install
```

### 2. Compile TypeSpec → OpenAPI

```bash
# Compile (tạo ra generated/openapi.yaml)
npx tsp compile library-api.tsp

# Hoặc watch mode (tự động compile khi file thay đổi)
npx tsp compile library-api.tsp --watch
```

### 3. Xem file OpenAPI được generate

```bash
# File output: generated/openapi.yaml
cat generated/openapi.yaml

# Render với Redocly
npx @redocly/cli preview-docs generated/openapi.yaml
```

### 4. VS Code Extension (khuyến nghị)

```bash
# Cài extension TypeSpec for VS Code
code --install-extension typespec.typespec-vscode
```

Extension cung cấp:
- Syntax highlighting
- IntelliSense / autocomplete
- Inline error checking
- Go to definition

### 5. Generate code từ OpenAPI output

```bash
# Sau khi compile TypeSpec → OpenAPI
# Dùng openapi-generator để gen code

npm install -g @openapitools/openapi-generator-cli

# TypeScript client
openapi-generator-cli generate \
  -i generated/openapi.yaml \
  -g typescript-axios \
  -o ./generated/ts-client

# Python client
openapi-generator-cli generate \
  -i generated/openapi.yaml \
  -g python \
  -o ./generated/python-client
```

### 6. Format và lint TypeSpec

```bash
# Format code
npx tsp format library-api.tsp

# Check errors
npx tsp compile library-api.tsp --no-emit
```

---

## Tính năng TypeSpec nổi bật trong file này

### Generic Types
```typescript
// Tái sử dụng wrapper cho mọi response
model PagedResponse<T> {
  data: T[];
  pagination: Pagination;
}

// Sử dụng
interface Books {
  list(): PagedResponse<Book>;  // → { data: Book[], pagination: ... }
}
```

### Decorators
```typescript
@minLength(1) @maxLength(255) title: string;
@pattern("^\\d{13}$") isbn: string;
@minValue(0) availableCopies: int32;
```

### Multi-status Responses
```typescript
create(): 
  | { @statusCode statusCode: 201; @body body: ItemResponse<Book>; }
  | { @statusCode statusCode: 400; @body body: ApiError; }
  | { @statusCode statusCode: 409; @body body: ApiError; };
```

### Interface-based Organization
```typescript
@route("/books") @tag("books")
interface Books {
  @get list(...): ...;
  @post create(...): ...;
  @get @route("/{id}") get(...): ...;
}
```

## Cấu trúc thư mục

```
typspec/
├── library-api.tsp      # TypeSpec source (đây là file bạn chỉnh sửa)
├── tspconfig.yaml       # Config: output format, output path
├── package.json         # Dependencies
├── README.md            # File này
└── generated/           # Generated output (gitignore)
    └── openapi.yaml     # OpenAPI 3.x output (auto-generated)
```

## Công cụ liên quan

| Công cụ | Mục đích | Link |
|---------|----------|------|
| TypeSpec Compiler | Compile .tsp → OpenAPI | https://typespec.io |
| VS Code Extension | IDE support | typespec.typespec-vscode |
| Azure TypeSpec | Azure REST API guideline | https://azure.github.io/typespec-azure |
| typespec-go | Generate Go code | https://github.com/microsoft/typespec-go |
