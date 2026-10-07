destiny_add_executable(test "${CMAKE_CURRENT_LIST_DIR}/src/main.cpp")
set_target_properties(
        test
        PROPERTIES
        CXX_STANDARD 20
        CXX_STANDARD_REQUIRED ON
)
target_link_libraries(test PRIVATE destiny_core_cpuManager)