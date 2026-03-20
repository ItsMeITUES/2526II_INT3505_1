import "@typespec/http";
import "@typespec/rest";
import "@typespec/openapi3";

using TypeSpec.Http;
using TypeSpec.Rest;

/**
 * Library Management API
 *
 * TypeSpec (formerly CADL) là ngôn ngữ mô tả API của Microsoft,
 * dùng cú pháp TypeScript-like với type system mạnh mẽ.
 * TypeSpec compile ra OpenAPI, JSON Schema, Protobuf, v.v.
 */
@service({
  title: "Library Management API",
  version: "1.0.0",
})
@server("http://localhost:3000/api/v1", "Development server")
@server("https://api.library.example.com/v1", "Production server")
namespace LibraryAPI;

// ─── ENUMS ───────────────────────────────────────────────────────────────────

/** Danh mục sách */
enum Category {
  Fiction: "fiction",
  NonFiction: "non-fiction",
  Science: "science",
  History: "history",
  Technology: "technology",
}

/** Loại thành viên */
enum MembershipType {
  Basic: "basic",
  Premium: "premium",
  Student: "student",
}

/** Trạng thái phiếu mượn */
enum LoanStatus {
  Active: "active",
  Returned: "returned",
  Overdue: "overdue",
}

/** Tình trạng sách khi trả */
enum BookCondition {
  Good: "good",
  Damaged: "damaged",
  Lost: "lost",
}

// ─── MODELS ──────────────────────────────────────────────────────────────────

/** Thông tin phân trang */
model Pagination {
  /** Trang hiện tại */
  page: int32;

  /** Số bản ghi mỗi trang */
  limit: int32;

  /** Tổng số bản ghi */
  total: int32;

  /** Tổng số trang */
  totalPages: int32;
}

/** Response wrapper với data và phân trang */
model PagedResponse<T> {
  data: T[];
  pagination: Pagination;
}

/** Response wrapper cho single item */
model ItemResponse<T> {
  data: T;
}

/** Model lỗi chuẩn */
model ApiError {
  /** Mã lỗi */
  error: string;

  /** Thông điệp lỗi */
  message: string;

  /** Chi tiết lỗi validation */
  details?: ValidationDetail[];
}

model ValidationDetail {
  field: string;
  message: string;
}

/** Thông tin sách trong thư viện */
model Book {
  /** ID duy nhất của sách */
  id: string;

  /** Tên sách */
  @minLength(1)
  @maxLength(255)
  title: string;

  /** Tác giả */
  @minLength(1)
  @maxLength(255)
  author: string;

  /** Mã ISBN 13 chữ số */
  @pattern("^\\d{13}$")
  isbn: string;

  /** Danh mục sách */
  category: Category;

  /** Tổng số bản */
  @minValue(1)
  totalCopies: int32;

  /** Số bản còn có thể mượn */
  @minValue(0)
  availableCopies: int32;

  /** Năm xuất bản */
  @minValue(1000)
  @maxValue(2100)
  publishedYear?: int32;

  /** Mô tả sách */
  @maxLength(2000)
  description?: string;

  createdAt: utcDateTime;
  updatedAt: utcDateTime;
}

/** Payload tạo sách mới */
model CreateBookRequest {
  @minLength(1)
  @maxLength(255)
  title: string;

  @minLength(1)
  @maxLength(255)
  author: string;

  @pattern("^\\d{13}$")
  isbn: string;

  category: Category;

  @minValue(1)
  totalCopies: int32;

  publishedYear?: int32;

  @maxLength(2000)
  description?: string;
}

/** Payload cập nhật sách (tất cả fields optional) */
model UpdateBookRequest {
  @minLength(1)
  @maxLength(255)
  title?: string;

  author?: string;
  category?: Category;

  @minValue(1)
  totalCopies?: int32;

  publishedYear?: int32;
  description?: string;
}

/** Thông tin thành viên */
model Member {
  id: string;

  @minLength(2)
  @maxLength(100)
  name: string;

  email: string;
  phone?: string;
  membershipType: MembershipType;
  membershipExpiry: plainDate;

  @minValue(0)
  activeLoansCount: int32;

  createdAt: utcDateTime;
}

/** Payload đăng ký thành viên mới */
model CreateMemberRequest {
  @minLength(2)
  @maxLength(100)
  name: string;

  email: string;
  phone?: string;
  membershipType: MembershipType;
}

/** Phiếu mượn sách */
model Loan {
  id: string;
  bookId: string;
  book?: Book;
  memberId: string;
  member?: Member;
  borrowedAt: plainDate;
  dueDate: plainDate;
  returnedAt?: plainDate | null;
  status: LoanStatus;
  condition?: BookCondition | null;
}

/** Payload tạo phiếu mượn */
model CreateLoanRequest {
  bookId: string;
  memberId: string;

  /** Hạn trả. Mặc định: 14 ngày từ hôm nay */
  dueDate?: plainDate;
}

/** Payload trả sách */
model ReturnBookRequest {
  /** Ngày trả thực tế. Mặc định: hôm nay */
  returnedAt?: plainDate;

  /** Tình trạng sách khi trả. Mặc định: good */
  condition?: BookCondition;
}

// ─── INTERFACES (Controllers) ─────────────────────────────────────────────────

/**
 * Quản lý sách
 */
@route("/books")
@tag("books")
interface Books {
  /** Lấy danh sách sách với phân trang và bộ lọc */
  @get
  list(
    @query page?: int32 = 1,
    @query limit?: int32 = 20,
    @query search?: string,
    @query category?: Category,
    @query available?: boolean,
  ): PagedResponse<Book>;

  /** Thêm sách mới vào thư viện */
  @post
  create(@body book: CreateBookRequest):
    | {
        @statusCode statusCode: 201;
        @body body: ItemResponse<Book>;
      }
    | {
        @statusCode statusCode: 400;
        @body body: ApiError;
      }
    | {
        @statusCode statusCode: 409;
        @body body: ApiError;
      };

  /** Xem thông tin chi tiết sách */
  @get
  @route("/{bookId}")
  get(@path bookId: string):
    | ItemResponse<Book>
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      };

  /** Cập nhật thông tin sách */
  @put
  @route("/{bookId}")
  update(@path bookId: string, @body book: UpdateBookRequest):
    | ItemResponse<Book>
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      };

  /** Xóa sách khỏi thư viện */
  @delete
  @route("/{bookId}")
  delete(@path bookId: string):
    | {
        @statusCode statusCode: 204;
      }
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      }
    | {
        @statusCode statusCode: 409;
        @body body: ApiError;
      };
}

/**
 * Quản lý thành viên
 */
@route("/members")
@tag("members")
interface Members {
  /** Lấy danh sách thành viên */
  @get
  list(
    @query page?: int32 = 1,
    @query limit?: int32 = 20,
    @query search?: string,
  ): PagedResponse<Member>;

  /** Đăng ký thành viên mới */
  @post
  create(@body member: CreateMemberRequest):
    | {
        @statusCode statusCode: 201;
        @body body: ItemResponse<Member>;
      }
    | {
        @statusCode statusCode: 400;
        @body body: ApiError;
      }
    | {
        @statusCode statusCode: 409;
        @body body: ApiError;
      };

  /** Xem thông tin thành viên */
  @get
  @route("/{memberId}")
  get(@path memberId: string):
    | ItemResponse<Member>
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      };

  /** Lịch sử mượn sách của thành viên */
  @get
  @route("/{memberId}/loans")
  getLoans(
    @path memberId: string,
    @query status?: LoanStatus,
    @query page?: int32 = 1,
    @query limit?: int32 = 20,
  ): PagedResponse<Loan>;
}

/**
 * Quản lý phiếu mượn và trả sách
 */
@route("/loans")
@tag("loans")
interface Loans {
  /** Lấy tất cả phiếu mượn */
  @get
  list(
    @query status?: LoanStatus,
    @query page?: int32 = 1,
    @query limit?: int32 = 20,
  ): PagedResponse<Loan>;

  /** Tạo phiếu mượn sách mới */
  @post
  create(@body loan: CreateLoanRequest):
    | {
        @statusCode statusCode: 201;
        @body body: ItemResponse<Loan>;
      }
    | {
        @statusCode statusCode: 400;
        @body body: ApiError;
      }
    | {
        @statusCode statusCode: 422;
        @body body: ApiError;
      };

  /** Xem thông tin phiếu mượn */
  @get
  @route("/{loanId}")
  get(@path loanId: string):
    | ItemResponse<Loan>
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      };

  /** Xác nhận trả sách */
  @post
  @route("/{loanId}/return")
  returnBook(@path loanId: string, @body body: ReturnBookRequest):
    | ItemResponse<Loan>
    | {
        @statusCode statusCode: 404;
        @body body: ApiError;
      }
    | {
        @statusCode statusCode: 409;
        @body body: ApiError;
      };
}
