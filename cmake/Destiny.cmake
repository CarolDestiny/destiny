include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/DestinyRegistry.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/DestinyTargets.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/DestinyFacts.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/DestinyCompileContext.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/DestinyReport.cmake")

function(destiny_configure_project)
    destiny_collect_modules()
    set(manifest "${CMAKE_BINARY_DIR}/generated/modules.json")
    destiny_write_inventory("${manifest}")
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -B -m tool.auto_define_config
            --root "${DESTINY_PROJECT_ROOT}" --inventory "${manifest}" check
        WORKING_DIRECTORY "${DESTINY_PROJECT_ROOT}"
        RESULT_VARIABLE status OUTPUT_VARIABLE output ERROR_VARIABLE diagnostic)
    if(NOT status EQUAL 0)
        message(FATAL_ERROR "${diagnostic}")
    endif()
    destiny_prepare_compile_contexts()
    destiny_prepare_facts("${manifest}")
    get_property(modules GLOBAL PROPERTY DESTINY_MODULES)
    foreach(path IN LISTS modules)
        set(DESTINY_CURRENT_MODULE "${path}")
        add_subdirectory("${CMAKE_CURRENT_FUNCTION_LIST_DIR}/module" "${CMAKE_BINARY_DIR}/.obj/${path}")
    endforeach()
    _destiny_write_report()
endfunction()
