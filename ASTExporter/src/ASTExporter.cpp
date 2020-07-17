/*
 * ASTExporter.cpp
 *
 *  Created on: Jul 16, 2020
 *      Author: carson
 */
#include <clang/Tooling/CommonOptionsParser.h>
#include <clang/ASTMatchers/ASTMatchFinder.h>
#include <clang/Tooling/Tooling.h>
#include <llvm/ADT/SmallString.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/raw_ostream.h>
#include "llvm/Support/JSON.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include <iostream>
#include <Python.h>

using namespace llvm::json;
using namespace clang::tooling;
using JObject = llvm::json::Object;
using namespace clang;


//This is just here to build the options parser
//I could not find a way to just get the options parser to parse command line opts without
//also looking for a custom options category. :/
static llvm::cl::OptionCategory ASTExporterOptions("Export options");


/*
 * This is a simpler AST visitor that collects some information from nodes it vists
 * and records some information about the nodes. For search based repair, we are
 * not doing deep analysis of individual statements. Instead, we want to be able to access
 * functions, parameters, local/global variables, statements, and arguments passed to call exprs.
 * There might be some more info we need when dealing with templates etc.
 *
 * All information is just stored into a json object right now
 */
class ASTExporterVisitor : public clang::RecursiveASTVisitor<ASTExporterVisitor> {
	public:
	  explicit ASTExporterVisitor(ASTContext *Context, JObject& info)
	    : Context(Context), tree_info(info) {}

	  bool VisitStmt(Stmt * stmt) {
		  std::cout << "VISITED SOME STMT" << std::endl;
		  return true;
	  }

	  bool VisitVarDecl(VarDecl * vdecl) {
		  std::cout << "VISITED SOME VAR DECL" << std::endl;
		  return true;
	  }

	  bool VisitCallExpr(CallExpr * call_expr) {
		  std::cout << "VISITED SOME CALL EXPR" << std::endl;
		  return true;
	  }

	  bool VisitFunctionDecl(FunctionDecl * func_decl) {
		  std::cout << "VISITED SOME FUNCTION DECL" << std::endl;
		  return true;
	  }

	private:
	  ASTContext *Context;
	  JObject& tree_info;
};

/*
 * The Consumer/FrontendAction/Factory are all clang boilerplate
 * which allow us to trigger an action on the AST and pass variables up/down
 * the class hiearchy.
 */

class ASTExporterConsumer : public clang::ASTConsumer {
public:
  explicit ASTExporterConsumer(clang::ASTContext *Context, JObject& info)
    : Visitor(Context, info) {}

  virtual void HandleTranslationUnit(clang::ASTContext &Context) {
    Visitor.TraverseDecl(Context.getTranslationUnitDecl());
  }
private:
  ASTExporterVisitor Visitor;
};


class ASTExporterFrontendAction : public clang::ASTFrontendAction {
public:
	ASTExporterFrontendAction(JObject& json_info) : tree_info(json_info) {}
	std::unique_ptr<clang::ASTConsumer> CreateASTConsumer(
			clang::CompilerInstance &Compiler, llvm::StringRef InFile) {
		std::cout << "Creating AST Consumer!" << std::endl;
		return std::unique_ptr<clang::ASTConsumer>(
				new ASTExporterConsumer(&Compiler.getASTContext(), tree_info));
	}

private:
	JObject& tree_info;
};

class ASTExporterActionFactory : public FrontendActionFactory {
public:
	ASTExporterActionFactory(JObject& json_info) : tree_info(json_info) {}
	FrontendAction *create() {
		return new ASTExporterFrontendAction(tree_info);
	}

private:
	JObject& tree_info;
};

int main(int argc, const char * argv[]) {
	//TODO accept this from the binding the filename that is.
	CommonOptionsParser options_parser(argc, argv, ASTExporterOptions ,nullptr);
	//clang::tooling::runToolOnCode(&ASTExporterFrontend(), argv[1]);
	JObject tree_info;
	ClangTool tool(
			options_parser.getCompilations(), options_parser.getSourcePathList());
	ASTExporterActionFactory factory(tree_info);
	tool.run(&factory);
	return 0;
}
