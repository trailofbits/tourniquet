#include "ASTExporter.h"
ASTExporterVisitor::ASTExporterVisitor(ASTContext *Context, PyObject* info)
: Context(Context), tree_info(info), current_func(nullptr) {}

//TODO How to handle these types of errors in visitor and extension?
void ASTExporterVisitor::PyListAppendString(PyObject * list, std::string str) {
	PyObject* name_bytes = PyBytes_FromString(str.c_str());
	if (name_bytes == nullptr) {
		std::cout << "Failed to create PyString from StringName" << std::endl;
	}
	int ret = PyList_Append(list, name_bytes);
	if (ret == -1) {
		std::cout << "Failed to append StringName" << std::endl;
	}
}

void ASTExporterVisitor::PyDictUpdateEntry(PyObject * dict, PyObject * key, PyObject * new_item) {
	if (auto old_item = PyDict_GetItem(dict, key)) {
		if (PyList_Append(old_item, new_item) == -1) {
			std::cout << "Failed to update array entry!" << std::endl;
		}
	}
	else {
		//Always init to be [item]
		PyObject * arr = PyList_New(0);
		if (PyList_Append(arr, new_item) == -1) {
			std::cout << "Failed to append new_item to arr!" << std::endl;
		}
		PyDict_SetItem(dict, key, arr);
	}
}

bool ASTExporterVisitor::VisitDeclStmt(Stmt * stmt) {
	std::string expr = getText(*stmt, *Context);
	PyObject * func_key = PyBytes_FromString(current_func->getNameAsString().c_str());
	if (func_key == nullptr) {
		std::cout << "Failed to create PyString from FunctionName" << std::endl;
		return true;
	}
	PyObject * new_arr = PyList_New(0);
	if (new_arr == nullptr) {
		std::cout << "Failed to allocate PyList!" << std::endl;
		return true;
	}
	PyListAppendString(new_arr, expr);
	PyListAppendString(new_arr, "stmt_type");
	PyDictUpdateEntry(tree_info, func_key, new_arr);
	return true;
}

//Current func, var name, var type, qual types, string
//Down cast to other types of param decl?
//TODO test non canonical types
bool ASTExporterVisitor::VisitVarDecl(VarDecl * vdecl) {
	//Ignore externs, and parameter declarations.
	if (vdecl->getStorageClass() == SC_Extern || vdecl->isLocalVarDecl() == 0) {
		return true;
	}
	std::string fname = "global";
	auto parent_func = vdecl->getParentFunctionOrMethod();
	if (parent_func != nullptr) {
		FunctionDecl * fdecl = llvm::dyn_cast<FunctionDecl>(parent_func);
		fname = fdecl->getNameAsString();
	}
	PyObject * func_key = PyBytes_FromString(fname.c_str());
	if (func_key == nullptr) {
		std::cout << "Failed to create PyString from FunctionName" << std::endl;
		return true;
	}
	//Function name --> (var_name, type, is_arr, size)
	PyObject * new_arr = PyList_New(0);
	if (new_arr == nullptr) {
		std::cout << "Failed to allocate PyList!" << std::endl;
		return true;
	}
	PyListAppendString(new_arr, vdecl->getNameAsString());
	auto qt = vdecl->getType();
	if (auto arr_type = llvm::dyn_cast<ConstantArrayType>(qt.getTypePtr())) {
		auto size = arr_type->getSize().getSExtValue();
		std::string type = arr_type->getElementType().getAsString();
		PyListAppendString(new_arr, type);
		PyListAppendString(new_arr, "1");
		PyListAppendString(new_arr, std::to_string(size));
	}
	else {
		PyListAppendString(new_arr, qt.getAsString());
		PyListAppendString(new_arr, "0");
		auto type_info = Context->getTypeInfo(qt);
		PyListAppendString(new_arr, std::to_string(type_info.Width/8));
	}
	PyListAppendString(new_arr, "var_type");
	PyDictUpdateEntry(tree_info, func_key, new_arr);
	return true;
}

//Current func, Callee, args, arg types, string
bool ASTExporterVisitor::VisitCallExpr(CallExpr * call_expr) {
	std::string expr = getText(*call_expr, *Context);
	PyObject * func_key = PyBytes_FromString(current_func->getNameAsString().c_str());
	if (func_key == nullptr) {
		std::cout << "Failed to create PyString from FunctionName" << std::endl;
		return true;
	}
	PyObject * new_arr = PyList_New(0);
	if (new_arr == nullptr) {
		std::cout << "Failed to allocate PyList!" << std::endl;
		return true;
	}
	auto test = call_expr->getCallee();
	FunctionDecl *func = call_expr->getDirectCallee();
	std::string callee = func->getNameInfo().getName().getAsString();
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

//Name, Parameters, Parameter Types?
bool ASTExporterVisitor::VisitFunctionDecl(FunctionDecl * func_decl) {
	if (func_decl->getStorageClass() == SC_Extern) {
		return true;
	}
	current_func = func_decl;
	std::string expr = getText(*func_decl, *Context);
	//std::cout << "FuncDecl: " << func_decl->getNameAsString() << std::endl;
	//For each param, iterate through and have a visitor for that.
	//func_decl->getNumParams();
	return true;
}
