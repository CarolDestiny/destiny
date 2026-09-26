include_guard(GLOBAL)

function(_destiny_project_options output)
    set(options)
    if(DESTINY_NATIVE_OPTIMIZATION)
        list(APPEND options -march=native)
    endif()
    set(${output} "${options}" PARENT_SCOPE)
endfunction()

function(_destiny_system_definitions output)
    set(definitions)
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SIZEOF_VOID_P EQUAL 4)
        # off_t and ino_t must represent WSL/mounted-filesystem metadata consistently.
        list(APPEND definitions _FILE_OFFSET_BITS=64)
    endif()
    set(${output} "${definitions}" PARENT_SCOPE)
endfunction()

function(_destiny_system_usage target visibility)
    _destiny_system_definitions(definitions)
    target_compile_definitions("${target}" ${visibility} ${definitions})
endfunction()
