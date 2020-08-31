#define PY_SSIZE_T_CLEAN
#include "ASTExporter.h"
#include "ASTPatch.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>

/*
 * TODO Remove global and pass to frontend action instead
 */
PyObject *extract_results;

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
  const char *filename;
  if (!PyArg_ParseTuple(args, "s", &filename)) {
    PyErr_SetString(PyExc_TypeError, "Invalid arguments passed to extract_ast");
    Py_RETURN_NONE;
  }

  std::string data;
  if (!read_file_to_string(filename, data)) {
    PyErr_SetString(PyExc_IOError, "Failed to open file for extraction");
    Py_RETURN_NONE;
  }

  // Allocate dictionary to return to Python
  extract_results = PyDict_New();
  if (!extract_results) {
    PyErr_SetString(PyExc_MemoryError, "Allocation failed for dict");
    Py_RETURN_NONE;
  }
  PyDict_SetItem(extract_results, PyBytes_FromString("module_name"),
                 PyBytes_FromString(filename));
  // Run tool on code, I believe that runToolOnCode owns/calls delete on the
  // FrontendAction Get double free when deleting manually
  runToolOnCode(new ASTExporterFrontendAction(), data);
  // Return the python dictionary back to the python code.
  return extract_results;
}

static PyObject *transform(PyObject *self, PyObject *args) {
  int start_line, start_col, end_line, end_col;
  char *replacement;
  char *filename;
  if (!PyArg_ParseTuple(args, "s|s|i|i|i|i", &filename, &replacement,
                        &start_line, &start_col, &end_line, &end_col)) {
    PyErr_SetString(PyExc_TypeError, "Invalid arguments passed to transform");
    Py_RETURN_FALSE;
  }

  std::string data;
  if (!read_file_to_string(filename, data)) {
    PyErr_SetString(PyExc_IOError, "Failed to open file for patching");
    Py_RETURN_NONE;
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
    {NULL, NULL, 0, NULL},
};

struct PyModuleDef extractor_definition = {
    PyModuleDef_HEAD_INIT,
    "extractor",
    "The extractor extension uses clang to extract AST information and perform "
    "transformations",
    -1,
    extractor_methods,
};

extern "C" PyMODINIT_FUNC PyInit_extractor(void) {
  Py_Initialize();
  PyObject *m = PyModule_Create(&extractor_definition);
  return m;
}
