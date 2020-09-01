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

void ASTExporterVisitor::AddGlobalVarDecl(PyObject *var_decl_list) {
  PyDictUpdateEntry(tree_info, "globals", var_decl_list);
}

bool ASTExporterVisitor::VisitDeclStmt(Stmt *stmt) {
  std::string expr = getText(*stmt, *Context);
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

  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));
  PyList_Append(new_arr, PyUnicode_FromString(expr.c_str()));
  PyList_Append(new_arr, PyUnicode_FromString("stmt_type"));
  PyDictUpdateEntry(tree_info, current_func->getNameAsString().c_str(),
                    new_arr);
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
  PyList_Append(new_arr, PyUnicode_FromString("var_type"));
  PyDictUpdateEntry(tree_info, fname.c_str(), new_arr);
  return true;
}

// Current func, Callee, args, arg types, string
bool ASTExporterVisitor::VisitCallExpr(CallExpr *call_expr) {
  std::string expr = getText(*call_expr, *Context);

  PyObject *new_arr = PyList_New(0);
  if (new_arr == nullptr) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for list");
    return true;
  }

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

  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(start_col));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_line));
  PyList_Append(new_arr, PyLong_FromUnsignedLong(end_col));
  PyList_Append(new_arr, PyUnicode_FromString(expr.c_str()));
  PyList_Append(new_arr, PyUnicode_FromString(callee.c_str()));

  for (auto arg : call_expr->arguments()) {
    std::string arg_str = getText(*arg, *Context);
    PyList_Append(new_arr, PyUnicode_FromString(arg_str.c_str()));
    PyList_Append(new_arr,
                  PyUnicode_FromString(arg->getType().getAsString().c_str()));
  }
  PyList_Append(new_arr, PyUnicode_FromString("call_type"));
  PyDictUpdateEntry(tree_info, current_func->getNameAsString().c_str(),
                    new_arr);
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
