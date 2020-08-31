#include "ASTExporter.h"
ASTExporterVisitor::ASTExporterVisitor(ASTContext *Context, PyObject *info)
    : Context(Context), tree_info(info), current_func(nullptr) {}

// TODO How to handle these types of errors in visitor and extension?
void ASTExporterVisitor::PyListAppendString(PyObject *list, std::string str) {
  PyObject *name_bytes = PyBytes_FromString(str.c_str());
  if (name_bytes == nullptr) {
    // TODO(ww): ValueError or MemoryError here?
    PyErr_SetString(PyExc_ValueError,
                    "Failed to create bytes object from function name");
    return;
  }
  PyList_Append(list, name_bytes);
}

void ASTExporterVisitor::PyDictUpdateEntry(PyObject *dict, PyObject *key,
                                           PyObject *new_item) {
  if (auto old_item = PyDict_GetItem(dict, key)) {
    PyList_Append(old_item, new_item);
  } else {
    // Always init to be [item]
    PyObject *arr = PyList_New(0);
    PyList_Append(arr, new_item);
    PyDict_SetItem(dict, key, arr);
  }
}

bool ASTExporterVisitor::VisitDeclStmt(Stmt *stmt) {
  std::string expr = getText(*stmt, *Context);
  PyObject *func_key =
      PyBytes_FromString(current_func->getNameAsString().c_str());
  if (func_key == nullptr) {
    // TODO(ww): ValueError or MemoryError here?
    PyErr_SetString(PyExc_ValueError,
                    "Failed to create bytes object from function name");
    return true;
  }
  PyObject *new_arr = PyList_New(0);
  if (new_arr == nullptr) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for list");
    return true;
  }
  unsigned int start_line =
      Context->getSourceManager().getExpansionLineNumber(stmt->getBeginLoc());
  unsigned int start_col =
      Context->getSourceManager().getExpansionColumnNumber(stmt->getBeginLoc());
  unsigned int end_line =
      Context->getSourceManager().getExpansionLineNumber(stmt->getEndLoc());
  unsigned int end_col =
      Context->getSourceManager().getExpansionColumnNumber(stmt->getEndLoc());
  PyListAppendString(new_arr, std::to_string(start_line));
  PyListAppendString(new_arr, std::to_string(start_col));
  PyListAppendString(new_arr, std::to_string(end_line));
  PyListAppendString(new_arr, std::to_string(end_col));
  PyListAppendString(new_arr, expr);
  PyListAppendString(new_arr, "stmt_type");
  PyDictUpdateEntry(tree_info, func_key, new_arr);
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
  std::string fname = "global";
  auto parent_func = vdecl->getParentFunctionOrMethod();
  if (parent_func != nullptr) {
    FunctionDecl *fdecl = llvm::dyn_cast<FunctionDecl>(parent_func);
    if (fdecl->isFileContext()) {
      return true;
    }
    fname = fdecl->getNameAsString();
  }
  PyObject *func_key = PyBytes_FromString(fname.c_str());
  if (func_key == nullptr) {
    // TODO(ww): ValueError or MemoryError here?
    PyErr_SetString(PyExc_ValueError,
                    "Failed to create bytes object from function name");
    return true;
  }
  // Function name --> (var_name, type, is_arr, size)
  PyObject *new_arr = PyList_New(0);
  if (new_arr == nullptr) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for list");
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
  PyListAppendString(new_arr, std::to_string(start_line));
  PyListAppendString(new_arr, std::to_string(start_col));
  PyListAppendString(new_arr, std::to_string(end_line));
  PyListAppendString(new_arr, std::to_string(end_col));
  PyListAppendString(new_arr, vdecl->getNameAsString());
  auto qt = vdecl->getType();
  if (auto arr_type = llvm::dyn_cast<ConstantArrayType>(qt.getTypePtr())) {
    auto size = arr_type->getSize().getSExtValue();
    std::string type = arr_type->getElementType().getAsString();
    PyListAppendString(new_arr, type);
    PyListAppendString(new_arr, "1");
    PyListAppendString(new_arr, std::to_string(size));
  } else {
    PyListAppendString(new_arr, qt.getAsString());
    PyListAppendString(new_arr, "0");
    auto type_info = Context->getTypeInfo(qt);
    PyListAppendString(new_arr, std::to_string(type_info.Width / 8));
  }
  PyListAppendString(new_arr, "var_type");
  PyDictUpdateEntry(tree_info, func_key, new_arr);
  return true;
}

// Current func, Callee, args, arg types, string
bool ASTExporterVisitor::VisitCallExpr(CallExpr *call_expr) {
  std::string expr = getText(*call_expr, *Context);
  PyObject *func_key =
      PyBytes_FromString(current_func->getNameAsString().c_str());
  if (func_key == nullptr) {
    // TODO(ww): ValueError or MemoryError here?
    PyErr_SetString(PyExc_ValueError,
                    "Failed to create bytes object from function name");
    return true;
  }
  PyObject *new_arr = PyList_New(0);
  if (new_arr == nullptr) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for list");
    return true;
  }
  auto test = call_expr->getCallee();
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
  PyListAppendString(new_arr, std::to_string(start_line));
  PyListAppendString(new_arr, std::to_string(start_col));
  PyListAppendString(new_arr, std::to_string(end_line));
  // +1 here to catch the semi colon :)
  PyListAppendString(new_arr, std::to_string(end_col));
  PyListAppendString(new_arr, expr);
  PyListAppendString(new_arr, callee);
  for (auto arg : call_expr->arguments()) {
    std::string arg_str = getText(*arg, *Context);
    PyListAppendString(new_arr, arg_str);
    PyListAppendString(new_arr, arg->getType().getAsString());
  }
  PyListAppendString(new_arr, "call_type");
  PyDictUpdateEntry(tree_info, func_key, new_arr);
  return true;
}

// Name, Parameters, Parameter Types?
bool ASTExporterVisitor::VisitFunctionDecl(FunctionDecl *func_decl) {
  if (func_decl->getStorageClass() == SC_Extern) {
    return true;
  }
  current_func = func_decl;
  return true;
}
