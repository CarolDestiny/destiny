add_library(
        destiny_core_cpuAlloc
        STATIC
        "src/onload.cpp"
        "src/unload.cpp"
        "src/best_efficiency_cpu_core.cpp"
)

target_compile_features(destiny_core_cpuAlloc PUBLIC cxx_std_20)

destiny_map_headers(
        "core/cpuAlloc"
        cpu_alloc.hpp
        best_efficiency_cpu_core.hpp
        best_performance_cpu_core.hpp
)

target_include_directories(destiny_core_cpuAlloc PUBLIC
        "$<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>"
)

target_link_libraries(destiny_core_cpuAlloc PRIVATE destiny_define_platform)
target_link_libraries(destiny_core_cpuAlloc PRIVATE destiny_define_cpu)