cmake_minimum_required(VERSION 3.5)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-rtti -std=c++17")
find_package(PythonLibs REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})
set(LIBRARY_LIST
    clangAST
    clangASTMatchers
    clangAnalysis
    clangBasic
    clangDriver
    clangEdit
    clangFrontend
    clangFrontendTool
    clangLex
    clangParse
    clangSema
    clangEdit
    clangRewrite
    clangRewriteFrontend
    clangStaticAnalyzerFrontend
    clangStaticAnalyzerCheckers
    clangStaticAnalyzerCore
    clangCrossTU
    clangIndex
    clangSerialization
    clangToolingCore
    clangToolingInclusions
    clangTooling
    clangToolingRefactoring
    clangFormat
    ${PYTHON_LIBRARIES}
    )

find_package(LLVM 9.0 REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${LLVM_BUILD_MAIN_SRC_DIR}/tools/clang/include)
include_directories(${LLVM_BUILD_BINARY_DIR}/tools/clang/include)
link_directories(${LLVM_LIBRARY_DIRS})
add_definitions(${LLVM_DEFINITIONS})

add_definitions(-D__STDC_LIMIT_MACROS -D__STDC_CONSTANT_MACROS)

add_executable(
  ${PROJECT_NAME}
	ASTExporter.cpp
  )

target_link_libraries(${PROJECT_NAME} -Wl,--start-group ${LIBRARY_LIST} -Wl,--end-group)

target_link_libraries(${PROJECT_NAME} LLVM pthread m)
