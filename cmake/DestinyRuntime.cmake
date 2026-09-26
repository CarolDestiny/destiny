include_guard(GLOBAL)

function(_destiny_stage_runtime target)
    if(NOT WIN32)
        return()
    endif()
    set(extra)
    foreach(directory IN LISTS DESTINY_RUNTIME_DIRS)
        list(APPEND extra --runtime-dir "${directory}")
    endforeach()
    add_custom_command(TARGET "${target}" POST_BUILD
        COMMAND "${Python3_EXECUTABLE}" -B -m tool.build_support.runtime
            --executable "$<TARGET_FILE:${target}>"
            --compiler "${CMAKE_CXX_COMPILER}" --build-root "${CMAKE_BINARY_DIR}" ${extra}
        WORKING_DIRECTORY "${DESTINY_PROJECT_ROOT}" VERBATIM)
endfunction()
