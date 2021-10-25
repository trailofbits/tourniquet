#define PY_SSIZE_T_CLEAN
#include "ASTExporter.h"
#include "ASTPatch.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <utility>

static bool read_file_to_string(const std::string &filename,
                                std::string &data) {
  std::ifstream file(filename);
  if (!file.is_open()) {
    return false;
  }

  std::stringstream buf;
  buf << file.rdbuf();
  data = buf.str();

  return true;
}

template <class Tool, class... ToolArgs>
static void run_clang_tool(std::string &data, int is_cxx,
                           ToolArgs &&...tool_args) {
  std::vector<std::string> args{"-x"};
  if (is_cxx) {
    args.push_back("c++");
  } else {
    args.push_back("c");
  }

#if LLVM_VERSION_MAJOR <= 9
  runToolOnCodeWithArgs(new Tool(std::forward<ToolArgs>(tool_args)...), data,
                        args);
#else
  runToolOnCodeWithArgs(std::make_unique<Tool>(tool_args...), data, args);
#endif
}

static PyObject *extract_ast(PyObject *self, PyObject *args) {
  PyObject *filename_bytes;
  int is_cxx;
  if (!PyArg_ParseTuple(args, "O&p", PyUnicode_FSConverter, &filename_bytes,
                        &is_cxx)) {
    return nullptr;
  }

  std::string filename = PyBytes_AsString(filename_bytes);
  Py_DECREF(filename_bytes);

  std::string data;
  if (!read_file_to_string(filename, data)) {
    PyErr_SetString(PyExc_IOError, "Failed to open file for extraction");
    return nullptr;
  }

  // Allocate dictionary to return to Python
  PyObject *extract_results = PyDict_New();
  if (!extract_results) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for dict");
    return nullptr;
  }
  PyDict_SetItem(extract_results, PyUnicode_FromString("module_name"),
                 PyUnicode_FromString(filename.c_str()));

  run_clang_tool<ASTExporterFrontendAction>(data, is_cxx, extract_results);

  // Return the python dictionary back to the python code.
  return extract_results;
}

static PyObject *transform(PyObject *self, PyObject *args) {
  PyObject *filename_bytes;
  char *replacement;
  int is_cxx;
  int start_line, start_col, end_line, end_col;
  if (!PyArg_ParseTuple(args, "O&psiiii", PyUnicode_FSConverter,
                        &filename_bytes, &is_cxx, &replacement, &start_line,
                        &start_col, &end_line, &end_col)) {
    return nullptr;
  }

  std::string filename = PyBytes_AsString(filename_bytes);
  Py_DECREF(filename_bytes);

  std::string data;
  if (!read_file_to_string(filename, data)) {
    PyErr_SetString(PyExc_IOError, "Failed to open file for patching");
    return nullptr;
  }

  run_clang_tool<ASTPatchAction>(data, is_cxx, start_line, start_col, end_line,
                                 end_col, std::string(replacement), filename);

  // The patching action might have failed (and set an appropriate Python
  // exception) on an I/O error. If so, return nullptr and allow the exception
  // to propagate.
  if (PyErr_Occurred()) {
    return nullptr;
  }

  Py_RETURN_TRUE;
}

PyMethodDef extractor_methods[] = {
    {"extract_ast", extract_ast, METH_VARARGS,
     "Returns a dictionary containing AST info for a file"},
    {"transform", transform, METH_VARARGS,
     "Transforms the target program with a replacement"},
    {nullptr, nullptr, 0, nullptr},
};

static struct PyModuleDef extractor_definition = {
    PyModuleDef_HEAD_INIT,
    "extractor",
    "The extractor extension uses clang to extract AST information and perform "
    "transformations",
    -1,
    extractor_methods,
};

PyMODINIT_FUNC PyInit_extractor(void) {
  PyObject *m = PyModule_Create(&extractor_definition);
  return m;
}
