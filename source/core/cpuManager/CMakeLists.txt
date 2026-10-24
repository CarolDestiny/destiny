add_library(
        destiny_core_cpuManager
        STATIC
        "src/onload.cpp"
        "src/unload.cpp"
        "src/cpu_manager.cpp"

        "src/best_efficiency_cpu_core.cpp"

        "src/thread_local_buffer/thread_local_buffer.cpp"

        "src/coroutine_manager/coroutine.cpp"
        "src/coroutine_manager/coroutine_manager.cpp"
)

target_compile_features(destiny_core_cpuManager PUBLIC cxx_std_20)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(destiny_core_cpuManager PRIVATE Threads::Threads)

destiny_map_headers(
        destiny_core_cpuManager
        "core/cpuManager"
        cpu_manager.hpp
        best_efficiency_cpu_core.hpp
        best_performance_cpu_core.hpp

        promise_local.hpp
        coroutine_manager.hpp
)

target_include_directories(destiny_core_cpuManager PUBLIC
        "$<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>"
)

target_link_libraries(destiny_core_cpuManager PRIVATE destiny_define_access)
target_link_libraries(destiny_core_cpuManager PRIVATE destiny_define_platform)
target_link_libraries(destiny_core_cpuManager PRIVATE destiny_define_cpu)
