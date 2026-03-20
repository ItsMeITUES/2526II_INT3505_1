import "@typespec/http";
using Http;

@service({ title: "Library API" })
namespace Library;

model Book { id: int32; title: string; }

@route("/books")
interface Books {
  @get list(): Book[];
}