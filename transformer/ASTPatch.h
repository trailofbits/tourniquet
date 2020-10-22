/*
 * ASTTransformer.cpp
 *
 *  Created on: Aug 18, 2020
 *      Author: carson
 */

#pragma once

#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Lex/Lexer.h"
#include "clang/Rewrite/Core/Rewriter.h"

#include "clang/Lex/Lexer.h"
#if LLVM_VERSION_MAJOR <= 9
#include "clang/Tooling/Refactoring/SourceCode.h"
#else
#include "clang/Tooling/Transformer/SourceCode.h"
#endif

#include "llvm/Support/JSON.h"
#include <clang/ASTMatchers/ASTMatchFinder.h>
#include <clang/Tooling/CommonOptionsParser.h>
#include <clang/Tooling/Tooling.h>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <llvm/ADT/SmallString.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/raw_ostream.h>

#include <Python.h>

using namespace clang;
using namespace llvm;

class ASTPatchConsumer : public clang::ASTConsumer {
public:
  explicit ASTPatchConsumer(clang::ASTContext *Context, Rewriter *rewriter,
                            int start_line, int start_col, int end_line,
                            int end_col, std::string replacement) {
    SourceManager &srcMgr = rewriter->getSourceMgr();
    FileID id = rewriter->getSourceMgr().getMainFileID();
    const FileEntry *entry = rewriter->getSourceMgr().getFileEntryForID(id);
    SourceLocation start_loc =
        srcMgr.translateFileLineCol(entry, start_line, start_col);
    SourceLocation end_loc =
        srcMgr.translateFileLineCol(entry, end_line, end_col);
    SourceRange src_range(start_loc, end_loc);
    rewriter->ReplaceText(src_range, replacement.c_str());
  }
};

class ASTPatchAction : public ASTFrontendAction {
public:
  explicit ASTPatchAction(int start_line, int start_col, int end_line,
                          int end_col, std::string replacement,
                          std::string filepath)
      : start_line(start_line), start_col(start_col), end_line(end_line),
        end_col(end_col), replacement(replacement), filepath(filepath) {}

  ASTPatchAction(const ASTPatchAction &) = delete;
  ASTPatchAction &operator=(const ASTPatchAction &) = delete;

  // TODO There is probably a better place to do this, HandleTranslationUnit
  // maybe?
  // TODO Best way to handle errors?
  void EndSourceFileAction() override {
    FileID id = rewriter.getSourceMgr().getMainFileID();
    const FileEntry *Entry = rewriter.getSourceMgr().getFileEntryForID(id);
    std::string string_buffer;
    llvm::raw_string_ostream output_stream(string_buffer);
    rewriter.getRewriteBufferFor(id)->write(output_stream);
    std::ofstream ofs(filepath, std::ofstream::trunc);
    if (ofs.is_open()) {
      ofs << output_stream.str();
    } else {
      PyErr_SetString(PyExc_IOError, "Failed to open file for patching");
    }
  }

  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &Compiler,
                                                 StringRef file) override {
    rewriter.setSourceMgr(Compiler.getSourceManager(), Compiler.getLangOpts());
    return std::unique_ptr<clang::ASTConsumer>(
        new ASTPatchConsumer(&Compiler.getASTContext(), &rewriter, start_line,
                             start_col, end_line, end_col, replacement));
  }

private:
  Rewriter rewriter;
  int start_line, start_col, end_line, end_col;
  std::string replacement;
  std::string filepath;
};
