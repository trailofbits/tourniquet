cmake_minimum_required(VERSION 3.10.2)
project(example)

set(SOURCE_DIR "transformer")
include_directories(${SOURCE_DIR})

if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(MACOSX TRUE)
endif()
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
find_package(PythonLibs REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

find_package(LLVM 9.0 REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${LLVM_BUILD_MAIN_SRC_DIR}/tools/clang/include)
include_directories(${LLVM_BUILD_BINARY_DIR}/tools/clang/include)
link_directories(${LLVM_LIBRARY_DIRS})
add_definitions(${LLVM_DEFINITIONS})

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
add_definitions(-D__STDC_LIMIT_MACROS -D__STDC_CONSTANT_MACROS)

add_library(
	${PROJECT_NAME}
	SHARED
	${SOURCE_DIR}/ASTExporter.cpp
	${SOURCE_DIR}/extractor.cpp
  )
set_target_properties(
	${PROJECT_NAME}
	PROPERTIES
		PREFIX ""
		OUTPUT_NAME ${PYTHON_MODULE_NAME}
)

if (MACOSX)
	target_link_libraries(${PROJECT_NAME} ${LIBRARY_LIST})
else()
	target_link_libraries(${PROJECT_NAME} -Wl,--start-group ${LIBRARY_LIST} -Wl,--end-group)
endif()
target_link_libraries(${PROJECT_NAME} LLVM pthread m)
