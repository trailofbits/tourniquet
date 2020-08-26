#define PY_SSIZE_T_CLEAN
#include "ASTExporter.h"
#include "ASTPatch.h"
#include <fstream>
#include <iostream>
#include <memory>
/*
 * TODO Remove global and pass to frontend action instead
 */
PyObject *extract_results;

static PyObject *extract_ast(PyObject *self, PyObject *args) {
  const char *filename;
  if (!PyArg_ParseTuple(args, "s", &filename)) {
    std::cout << "Failed to parse arguments to C extension" << std::endl;
    Py_RETURN_NONE;
  }

  std::ifstream file(filename);
  if (!file.is_open()) {
    std::cout << "Failed to find file!" << std::endl;
    Py_RETURN_NONE;
  }

  // Parse code into a string
  std::string data = "";
  std::string curr_line;
  while (getline(file, curr_line)) {
    data += curr_line + '\n';
  }
  file.close();

  // Allocate dictionary to return to Python
  extract_results = PyDict_New();
  if (!extract_results) {
    std::cout << "Error creating PyDict!" << std::endl;
    Py_RETURN_NONE;
  }
  PyDict_Clear(extract_results);
  PyObject *mod_key = PyBytes_FromString("module_name");
  PyObject *file_info = PyBytes_FromString(filename);
  PyObject *arr1 = PyList_New(0);
  PyObject *arr2 = PyList_New(0);
  PyList_Append(arr1, file_info);
  PyList_Append(arr2, arr1);
  PyDict_SetItem(extract_results, mod_key, arr2);
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
    std::cout << "Failed to parse arguments to C extension" << std::endl;
    Py_RETURN_FALSE;
  }
  std::ifstream file(filename);
  if (!file.is_open()) {
    std::cout << "Failed to find file!" << std::endl;
    Py_RETURN_NONE;
  }
  // Parse code into a string
  std::string data = "";
  std::string curr_line;
  while (getline(file, curr_line)) {
    data += curr_line + '\n';
  }
  file.close();
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
