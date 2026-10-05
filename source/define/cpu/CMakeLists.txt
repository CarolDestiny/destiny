execute_process(
        COMMAND
        python
        "${CMAKE_CURRENT_LIST_DIR}/maintain/main.py"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/cpu/_python.hpp"
        WORKING_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}"
        RESULT_VARIABLE PYTHON_RESULT
        OUTPUT_VARIABLE PYTHON_OUTPUT
        ERROR_VARIABLE PYTHON_ERROR
)

if(NOT PYTHON_RESULT EQUAL 0)
    message(FATAL_ERROR "Python failed:\n${PYTHON_ERROR}")
endif()

add_library(destiny_define_cpu INTERFACE)

target_include_directories(
        destiny_define_cpu
        INTERFACE
        $<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>
)

file(MAKE_DIRECTORY "${DESTINY_INCLUDE_ROOT}/destiny/define/cpu")

file(
        CREATE_LINK
        "${CMAKE_CURRENT_SOURCE_DIR}/include/cpu.hpp"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/cpu/cpu.hpp"
        SYMBOLIC
)