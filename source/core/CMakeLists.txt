add_library(
        destiny_core
        STATIC
        "src/core.cpp"
        "src/onload.cpp"
        "src/unload.cpp"
)

target_compile_features(destiny_core PUBLIC cxx_std_20)

find_package(Threads REQUIRED)
target_link_libraries(destiny_core PRIVATE Threads::Threads)

destiny_map_headers(
        destiny_core
        "core"
        core.hpp
)

target_include_directories(destiny_core PUBLIC "$<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>")

target_link_libraries(destiny_core PRIVATE destiny_define_access)
target_link_libraries(destiny_core PRIVATE destiny_define_platform)
target_link_libraries(destiny_core PRIVATE destiny_define_cpu)