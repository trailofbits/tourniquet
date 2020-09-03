#define PY_SSIZE_T_CLEAN
#include "ASTExporter.h"
#include "ASTPatch.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>

static bool read_file_to_string(const char *filename, std::string &data) {
  std::ifstream file(filename);
  if (!file.is_open()) {
    return false;
  }

  std::stringstream buf;
  buf << file.rdbuf();
  data = buf.str();

  return true;
}

static PyObject *extract_ast(PyObject *self, PyObject *args) {
  char *filename;
  int is_cxx;
  // NOTE(ww): Instead of parsing the filename as a string, should probably use
  // "O&" with PyUnicode_FSConverter()
  if (!PyArg_ParseTuple(args, "sp", &filename, &is_cxx)) {
    return nullptr;
  }

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
                 PyUnicode_FromString(filename));
  // Run tool on code, I believe that runToolOnCode owns/calls delete on the
  // FrontendAction Get double free when deleting manually
  runToolOnCode(new ASTExporterFrontendAction(extract_results), data);
  // Return the python dictionary back to the python code.
  return extract_results;
}

static PyObject *transform(PyObject *self, PyObject *args) {
  char *filename;
  char *replacement;
  int is_cxx;
  int start_line, start_col, end_line, end_col;
  if (!PyArg_ParseTuple(args, "spsiiii", &filename, &is_cxx, &replacement,
                        &start_line, &start_col, &end_line, &end_col)) {
    return nullptr;
  }

  std::string data;
  if (!read_file_to_string(filename, data)) {
    PyErr_SetString(PyExc_IOError, "Failed to open file for patching");
    return nullptr;
  }

  runToolOnCode(new ASTPatchAction(start_line, start_col, end_line, end_col,
                                   std::string(replacement),
                                   std::string(filename)),
                data);
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
  Py_Initialize();
  PyObject *m = PyModule_Create(&extractor_definition);
  return m;
}
