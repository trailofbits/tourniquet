#include "ASTExporter.h"

ASTExporterVisitor::ASTExporterVisitor(ASTContext *Context, PyObject *info)
    : Context(Context), tree_info(info), current_func(nullptr) {}

void ASTExporterVisitor::PyDictUpdateEntry(PyObject *dict, const char *key,
                                           PyObject *new_item) {
  if (auto old_item = PyDict_GetItemString(dict, key)) {
    PyList_Append(old_item, new_item);
  } else {
    // Always init to be [item]
    PyObject *arr = PyList_New(0);
    PyList_Append(arr, new_item);
    PyDict_SetItemString(dict, key, arr);
  }
}

void ASTExporterVisitor::AddGlobalEntry(PyObject *entry) {
  PyDictUpdateEntry(tree_info, "globals", entry);
}

void ASTExporterVisitor::AddFunctionEntry(const char *func_name,
                                          PyObject *entry) {
  if (auto functions = PyDict_GetItemString(tree_info, "functions")) {
    PyDictUpdateEntry(functions, func_name, entry);
  } else {
    functions = PyDict_New();
    PyDict_SetItemString(tree_info, "functions", functions);
    PyDictUpdateEntry(functions, func_name, entry);
  }
}

bool ASTExporterVisitor::VisitDeclStmt(Stmt *stmt) {
  std::string expr = getText(*stmt, *Context);

  unsigned int start_line =
      Context->getSourceManager().getExpansionLineNumber(stmt->getBeginLoc());
  unsigned int start_col =
      Context->getSourceManager().getExpansionColumnNumber(stmt->getBeginLoc());
  unsigned int end_line =
      Context->getSourceManager().getExpansionLineNumber(stmt->getEndLoc());
  unsigned int end_col =
      Context->getSourceManager().getExpansionColumnNumber(stmt->getEndLoc());

  PyObject *new_arr = PyList_New(0);
  PyList_Append(new_arr, PyUnicode_FromString("stmt_type"));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));
  PyList_Append(new_arr, PyUnicode_FromString(expr.c_str()));
  AddFunctionEntry(current_func->getNameAsString().c_str(), new_arr);
  return true;
}

// Current func, var name, var type, qual types, string
// Down cast to other types of param decl?
// TODO test non canonical types
bool ASTExporterVisitor::VisitVarDecl(VarDecl *vdecl) {
  // Ignore externs, and parameter declarations.
  if (vdecl->getStorageClass() == SC_Extern) {
    return true;
  }

  unsigned int start_line =
      Context->getSourceManager().getExpansionLineNumber(vdecl->getBeginLoc());
  unsigned int start_col = Context->getSourceManager().getExpansionColumnNumber(
      vdecl->getBeginLoc());
  unsigned int end_line =
      Context->getSourceManager().getExpansionLineNumber(vdecl->getEndLoc());
  unsigned int end_col =
      Context->getSourceManager().getExpansionColumnNumber(vdecl->getEndLoc());

  // This Python list object contains our variable declaration state,
  // with the following layout:
  // [
  //   "var_type", start_line, start_col, end_line, end_col,
  //   var_name, var_type, is_array, size
  // ]
  // The variable declaration is either added to the list under the "globals"
  // key or to its enclosing function, depending on whether it's in a function.

  PyObject *new_arr = PyList_New(0);
  PyList_Append(new_arr, PyUnicode_FromString("var_type"));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));
  PyList_Append(new_arr,
                PyUnicode_FromString(vdecl->getNameAsString().c_str()));

  auto qt = vdecl->getType();
  if (auto arr_type = llvm::dyn_cast<ConstantArrayType>(qt.getTypePtr())) {
    auto size = arr_type->getSize().getZExtValue();
    std::string type = arr_type->getElementType().getAsString();
    PyList_Append(new_arr, PyUnicode_FromString(type.c_str()));
    PyList_Append(new_arr, PyLong_FromUnsignedLong(1));
    PyList_Append(new_arr, PyLong_FromUnsignedLong(size));
  } else {
    PyList_Append(new_arr, PyUnicode_FromString(qt.getAsString().c_str()));
    PyList_Append(new_arr, PyLong_FromUnsignedLong(0));
    auto type_info = Context->getTypeInfo(qt);
    PyList_Append(new_arr, PyLong_FromUnsignedLong(type_info.Width / 8));
  }

  auto parent_func = vdecl->getParentFunctionOrMethod();
  if (parent_func == nullptr) {
    AddGlobalEntry(new_arr);
  } else {
    FunctionDecl *fdecl = llvm::dyn_cast<FunctionDecl>(parent_func);
    if (fdecl->isFileContext()) {
      return true;
    }
    AddFunctionEntry(fdecl->getNameAsString().c_str(), new_arr);
  }

  return true;
}

// Current func, Callee, args, arg types, string
bool ASTExporterVisitor::VisitCallExpr(CallExpr *call_expr) {
  std::string expr = getText(*call_expr, *Context);

  FunctionDecl *func = call_expr->getDirectCallee();
  std::string callee = func->getNameInfo().getName().getAsString();
  unsigned int start_line = Context->getSourceManager().getExpansionLineNumber(
      call_expr->getBeginLoc());
  unsigned int start_col = Context->getSourceManager().getExpansionColumnNumber(
      call_expr->getBeginLoc());
  unsigned int end_line = Context->getSourceManager().getExpansionLineNumber(
      call_expr->getEndLoc());
  unsigned int end_col = Context->getSourceManager().getExpansionColumnNumber(
      call_expr->getEndLoc());

  PyObject *new_arr = PyList_New(0);
  PyList_Append(new_arr, PyUnicode_FromString("call_type"));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));
  PyList_Append(new_arr, PyUnicode_FromString(expr.c_str()));
  PyList_Append(new_arr, PyUnicode_FromString(callee.c_str()));

  for (auto arg : call_expr->arguments()) {
    auto arg_arr = PyList_New(0);
    PyList_Append(arg_arr,
                  PyUnicode_FromString(getText(*arg, *Context).str().c_str()));
    PyList_Append(arg_arr,
                  PyUnicode_FromString(arg->getType().getAsString().c_str()));
    PyList_Append(new_arr, arg_arr);
  }
  AddFunctionEntry(current_func->getNameAsString().c_str(), new_arr);
  return true;
}

// Name, Parameters, Parameter Types?
bool ASTExporterVisitor::VisitFunctionDecl(FunctionDecl *func_decl) {
  if (func_decl->getStorageClass() == SC_Extern) {
    return true;
  }

  unsigned int start_line = Context->getSourceManager().getExpansionLineNumber(
      func_decl->getBeginLoc());
  unsigned int start_col = Context->getSourceManager().getExpansionColumnNumber(
      func_decl->getBeginLoc());
  unsigned int end_line = Context->getSourceManager().getExpansionLineNumber(
      func_decl->getEndLoc());
  unsigned int end_col = Context->getSourceManager().getExpansionColumnNumber(
      func_decl->getEndLoc());

  PyObject *new_arr = PyList_New(0);
  PyList_Append(new_arr, PyUnicode_FromString("func_decl"));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));

  AddFunctionEntry(func_decl->getNameAsString().c_str(), new_arr);

  // NOTE(ww) Subsequent visitor methods use this member to determine which
  // function they're in.
  current_func = func_decl;

  return true;
}
