cmake_minimum_required(VERSION 3.20)

project(
        destiny
        VERSION 0.1.0
        LANGUAGES C CXX
)

option(DESTINY_BUILD_TEST "Build tests executables" ON)
option(DESTINY_BUILD_BENCH "Build benchmarks executables" ON)
option(DESTINY_BUILD_DEMO "Build demos executables" ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(DESTINY_INCLUDE_ROOT "${CMAKE_BINARY_DIR}/include")

function(destiny_add_executable target_name)
    add_executable(${target_name} ${ARGN})
    set_target_properties(
            ${target_name}
            PROPERTIES
            VS_DEBUGGER_WORKING_DIRECTORY
            "${CMAKE_SOURCE_DIR}"
    )
endfunction()

function(destiny_map_headers module_path)
    foreach(header IN LISTS ARGN)
        set(destination
                "${DESTINY_INCLUDE_ROOT}/destiny/${module_path}/${header}"
        )

        get_filename_component(directory "${destination}" DIRECTORY)
        file(MAKE_DIRECTORY "${directory}")

        file(CREATE_LINK
                "${CMAKE_CURRENT_SOURCE_DIR}/include/${header}"
                "${destination}"
                SYMBOLIC
        )
    endforeach()
endfunction()

add_subdirectory(source)
