cmake_minimum_required(VERSION 3.10.2)
project(transformer)

set(SOURCE_DIR "transformer")
include_directories(${SOURCE_DIR})

if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(MACOSX TRUE)
endif()
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
find_package(
  Python3
  COMPONENTS Development
  REQUIRED)
include_directories(${Python3_INCLUDE_DIRS})
link_directories(${Python3_LIBRARY_DIRS})

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
    clangFormat)

if(NOT MACOSX)
  # NOTE(ww): For reasons that are unclear to me, macOS does *not* want
  # Python extensions to link to the Python development libraries directly.
  # Instead, it expects to resolve them dynamically via dynamic_lookup.
  # See target_link_options below.
  set(LIBRARY_LIST ${LIBRARY_LIST} ${Python3_LIBRARIES})
endif()

add_definitions(-D__STDC_LIMIT_MACROS -D__STDC_CONSTANT_MACROS)

add_library(${PROJECT_NAME} SHARED ${SOURCE_DIR}/ASTExporter.cpp
                                   ${SOURCE_DIR}/extractor.cpp)
set_target_properties(${PROJECT_NAME}
                      PROPERTIES PREFIX "" OUTPUT_NAME ${PYTHON_MODULE_NAME})

if(MACOSX)
  # NOTE(ww): See the conditional inclusion above.
  target_link_options(${PROJECT_NAME} PUBLIC -undefined dynamic_lookup)
  target_link_libraries(${PROJECT_NAME} ${LIBRARY_LIST})
  # NOTE(ww): Python extensions on macOS don't use .dylib.
  set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX ".so")
else()
  target_link_libraries(${PROJECT_NAME} -Wl,--start-group ${LIBRARY_LIST}
                        -Wl,--end-group)
endif()
target_link_libraries(${PROJECT_NAME} LLVM pthread m)
