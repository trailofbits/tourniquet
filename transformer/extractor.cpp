#define PY_SSIZE_T_CLEAN
#include "ASTExporter.h"
#include <iostream>
#include <fstream>
#include <memory>
/*
 * The Clang FrontendFactory classes maintain some internal state which causes issues with repeated invocations
 * (invoking old action classes)
 *
 * We bypass the factory by directly running an action on code
 *
 * The results are stored in this global with each run, which is returned
 */
PyObject * extract_results;

static PyObject *
extract_ast(PyObject *self, PyObject *args) {
	const char* filename;
	if (!PyArg_ParseTuple(args, "s", &filename)) {
		std::cout << "Failed to parse arguments to C extension" << std::endl;
		Py_RETURN_NONE;
	}

	std::ifstream file(filename);
	if (!file.is_open()) {
		std::cout << "Failed to find file!" << std::endl;
		Py_RETURN_NONE;
	}

	//Parse code into a string
	std::string data = "";
	std::string curr_line;
	while(getline(file, curr_line)) {
		data += curr_line + '\n';
	}
	file.close();

	//Allocate dictionary to return to Python
	extract_results = PyDict_New();
	if (!extract_results) {
		std::cout << "Error creating PyDict!" << std::endl;
		Py_RETURN_NONE;
	}
	PyDict_Clear(extract_results);

	//Run tool on code, I believe that runToolOnCode owns/calls delete on the FrontendAction
	//Get double free when deleting manually
    runToolOnCode(new ASTExporterFrontendAction(), data);
    //Return the python dictionary back to the python code.
	return extract_results;
}



PyMethodDef extractor_methods[] = {
		{"extract_ast", extract_ast, METH_VARARGS, "Returns a dictionary containing AST info for a file"},
		{NULL, NULL, 0, NULL},
};

struct PyModuleDef extractor_definition = {
		PyModuleDef_HEAD_INIT,
		"extractor",
		"The extractor extension uses clang to extract AST information and perform transformations",
		-1,
		extractor_methods,
};

extern "C" PyMODINIT_FUNC PyInit_extractor(void) {
	Py_Initialize();
	PyObject *m = PyModule_Create(&extractor_definition);
	return m;
}
