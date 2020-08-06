#define PY_SSIZE_T_CLEAN
#include <Python.h>
//#ifdef __cplusplus
//extern "C" {
//#endif


/*
static PyObject *
extract_ast(PyObject *self, PyObject *args) {

	 const char* name;

	    if (!PyArg_ParseTuple(args, "s", &name))
	        return NULL;

	    printf("Hello %s!\n", name);

	    Py_RETURN_NONE;
}


static PyObject *
transform(PyObject * self, PyObject * args) {
	 const char* name;

	    if (!PyArg_ParseTuple(args, "s", &name))
	        return NULL;

	    printf("Hello %s!\n", name);

	    Py_RETURN_NONE;
}

static PyMethodDef ASTMethods[] =
{
     {"extract_ast", extract_ast, METH_VARARGS, "Extract information about Stmts, VarDecls, FunctionDecls, etc from the clang AST"},
     {NULL, NULL, 0, NULL},
	 {"transform", transform, METH_VARARGS, "Apply a transformation to the target program"},
	 {NULL, NULL, 0, NULL}
};

static struct PyModuleDef patchermodule =
{
    PyModuleDef_HEAD_INIT,
    "patcher",
    "",
    -1,
    ASTMethods
};

PyMODINIT_FUNC
PyInit_patcher(void) {
	return PyModule_Create(&patchermodule);
}
*/

extern "C" PyObject *pants(PyObject *self, PyObject *args) {
  int input;
  if (!PyArg_ParseTuple(args, "i", &input)) {
    return NULL;
  }

  return PyLong_FromLong((long)input * (long)input);
}

PyMethodDef example_methods[] = {
    {"pants", pants, METH_VARARGS, "Returns a square of an integer"},
    {NULL, NULL, 0, NULL},
};

struct PyModuleDef example_definition = {
    PyModuleDef_HEAD_INIT,
    "example",
    "example module containing pants() function",
    -1,
    example_methods,
};

extern "C" PyMODINIT_FUNC PyInit_extractor(void) {
  Py_Initialize();
  PyObject *m = PyModule_Create(&example_definition);

  return m;
}

//#ifdef __cplusplus
//}
//#endif
