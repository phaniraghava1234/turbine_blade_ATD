cmake_minimum_required(VERSION 3.10)
project(TurbineCFDSolver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall")

# Find packages (optional, comment out if not available)
# find_package(CGNS QUIET)

# Source files
set(SOURCES
    turbine_cfd_solver.cpp
)

# Executable
add_executable(turbine_solver ${SOURCES})

# Link libraries if CGNS is found
# if(CGNS_FOUND)
#     target_include_directories(turbine_solver PRIVATE ${CGNS_INCLUDE_DIRS})
#     target_link_libraries(turbine_solver PRIVATE ${CGNS_LIBRARIES})
#     target_compile_definitions(turbine_solver PRIVATE USE_CGNS)
# endif()

# Installation
install(TARGETS turbine_solver DESTINATION bin)

# Build instructions message
message(STATUS "")
message(STATUS "========================================")
message(STATUS "Turbine CFD Solver Build Configuration")
message(STATUS "========================================")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "")
message(STATUS "To build:")
message(STATUS "  mkdir build && cd build")
message(STATUS "  cmake ..")
message(STATUS "  make")
message(STATUS "========================================")
message(STATUS "")
