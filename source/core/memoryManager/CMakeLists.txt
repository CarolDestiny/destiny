add_library(
        destiny_core_memoryManager
        STATIC
)

target_compile_features(destiny_core_memoryManager PUBLIC cxx_std_17)

destiny_map_headers(
        destiny_core_memoryManager
        "core/memoryManager"
)

target_include_directories(destiny_core_memoryManager PUBLIC
        "$<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>"
)

target_link_libraries(destiny_core_memoryManager PRIVATE destiny_core_cpuManager)
