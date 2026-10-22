add_library(destiny_define_access INTERFACE)

target_include_directories(
        destiny_define_access
        INTERFACE
        $<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>
)

destiny_map_headers(
        destiny_define_access
        "define/access"
        access.hpp
)