if(WIN32)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS true)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_LINUX false)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_MACOS false)
elseif(UNIX AND NOT APPLE)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS false)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_LINUX true)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_MACOS false)
elseif(APPLE)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_WINDOWS false)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_LINUX false)
    set(DESTINY_CMAKE_DEFINE_PLATFORM_MACOS true)
endif()

configure_file(
        "${CMAKE_CURRENT_LIST_DIR}/include/_cmake.hpp.in"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/platform/_cmake.hpp"
        @ONLY
)

add_library(destiny_define_platform INTERFACE)

target_include_directories(
        destiny_define_platform
        INTERFACE
        $<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>
)

file(MAKE_DIRECTORY "${DESTINY_INCLUDE_ROOT}/destiny/define/platform")

file(
        CREATE_LINK
        "${CMAKE_CURRENT_SOURCE_DIR}/include/platform.hpp"
        "${DESTINY_INCLUDE_ROOT}/destiny/define/platform/platform.hpp"
        SYMBOLIC
)
