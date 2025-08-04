# CMakeLists.txt for test_lib v2.0
cmake_minimum_required(VERSION 3.10)
project(test_lib_v2 VERSION 2.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set build type if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0 -DDEBUG")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -DNDEBUG")

# Enable compile commands for tools like clang
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Find source files
file(GLOB_RECURSE SOURCES "src/*.cpp")
file(GLOB_RECURSE HEADERS "include/*.hpp")

# Print found files for debugging
message(STATUS "Found source files: ${SOURCES}")
message(STATUS "Found header files: ${HEADERS}")

# Create shared library
add_library(test_v2_shared SHARED ${SOURCES})
target_include_directories(test_v2_shared PUBLIC 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_definitions(test_v2_shared PRIVATE -DBUILDING_SHARED_LIB)
set_target_properties(test_v2_shared PROPERTIES
    OUTPUT_NAME "test_v2"
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Create static library
add_library(test_v2_static STATIC ${SOURCES})
target_include_directories(test_v2_static PUBLIC 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
set_target_properties(test_v2_static PROPERTIES
    OUTPUT_NAME "test_v2"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

# Set library output directory
set_target_properties(test_v2_shared PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Find and link dependencies (example: threads)
find_package(Threads REQUIRED)
target_link_libraries(test_v2_shared Threads::Threads)
target_link_libraries(test_v2_static Threads::Threads)

# Optional: Add example executable
option(BUILD_EXAMPLES "Build example programs" OFF)
if(BUILD_EXAMPLES)
    add_executable(example_v2 examples/main.cpp)
    target_link_libraries(example_v2 test_v2_shared)
    target_include_directories(example_v2 PRIVATE include)
endif()

# Installation rules
include(GNUInstallDirs)

install(TARGETS test_v2_shared test_v2_static
    EXPORT test_v2_targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING PATTERN "*.hpp"
)

install(EXPORT test_v2_targets
    FILE test_v2_targets.cmake
    NAMESPACE test_v2::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/test_v2
)

# Create config file
include(CMakePackageConfigHelpers)
write_basic_package_version_file(
    test_v2_config_version.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/test_v2_config.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/test_v2_config.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/test_v2
    NO_SET_AND_CHECK_MACRO
    NO_CHECK_REQUIRED_COMPONENTS_MACRO
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/test_v2_config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/test_v2_config_version.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/test_v2
)

# Print build information
message(STATUS "")
message(STATUS "Project: ${PROJECT_NAME} v${PROJECT_VERSION}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "Build examples: ${BUILD_EXAMPLES}")
message(STATUS "")
