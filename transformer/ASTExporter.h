/*
 * ASTExporter.h
 *
 *  Created on: Aug 6, 2020
 *      Author: carson
 */

#ifndef TRANSFORMER_ASTEXPORTER_H_
#define TRANSFORMER_ASTEXPORTER_H_

#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Lex/Lexer.h"
#include "clang/Tooling/Refactoring/SourceCode.h"
#include "llvm/Support/JSON.h"
#include <clang/ASTMatchers/ASTMatchFinder.h>
#include <clang/Tooling/CommonOptionsParser.h>
#include <clang/Tooling/Tooling.h>
#include <fcntl.h>
#include <iostream>
#include <llvm/ADT/SmallString.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/raw_ostream.h>

#ifdef __APPLE__
#include <python3.8/Python.h>
#else
#include <Python.h>
#endif

using namespace llvm::json;
using namespace clang::tooling;
using JObject = llvm::json::Object;
using namespace clang;

/*
 * This is a simpler AST visitor that collects some information from nodes it
 * vists and records some information about the nodes. For search based repair,
 * we are not doing deep analysis of individual statements. Instead, we want to
 * be able to access functions, parameters, local/global variables, statements,
 * and arguments passed to call exprs. There might be some more info we need
 * when dealing with templates etc.
 *
 * All information is just stored into a json object right now
 */
class ASTExporterVisitor
    : public clang::RecursiveASTVisitor<ASTExporterVisitor> {
public:
  ASTExporterVisitor(ASTContext *Context, PyObject *info);
  bool VisitDeclStmt(Stmt *stmt);
  bool VisitVarDecl(VarDecl *vdecl);
  bool VisitCallExpr(CallExpr *call_expr);
  bool VisitFunctionDecl(FunctionDecl *func_decl);

private:
  void PyDictUpdateEntry(PyObject *dict, const char *key, PyObject *new_item);
  void AddGlobalVarDecl(PyObject *var_decl_list);

  ASTContext *Context;
  PyObject *tree_info;
  // Clang doesn't store parental relationships for statements (it does for
  // decls) Meaning from a CallExpr you cant find the Caller Function with any
  // get method etc. Just keep track of our current function as we traverse
  FunctionDecl *current_func;
};

/*
 * The Consumer/FrontendAction/Factory are all clang boilerplate
 * which allow us to trigger an action on the AST and pass variables up/down
 * the class hiearchy.
 */

class ASTExporterConsumer : public clang::ASTConsumer {
public:
  explicit ASTExporterConsumer(clang::ASTContext *Context, PyObject *info)
      : Visitor(Context, info) {}

  virtual void HandleTranslationUnit(clang::ASTContext &Context) {
    Visitor.TraverseDecl(Context.getTranslationUnitDecl());
  }

private:
  ASTExporterVisitor Visitor;
};

class ASTExporterFrontendAction : public clang::ASTFrontendAction {
public:
  std::unique_ptr<clang::ASTConsumer>
  CreateASTConsumer(clang::CompilerInstance &Compiler, llvm::StringRef InFile) {
    return std::unique_ptr<clang::ASTConsumer>(
        new ASTExporterConsumer(&Compiler.getASTContext(), extract_results_));
  }

  explicit ASTExporterFrontendAction(PyObject *extract_results)
      : extract_results_{extract_results} {}

private:
  PyObject *extract_results_;
};

#endif /* TRANSFORMER_ASTEXPORTER_H_ */
