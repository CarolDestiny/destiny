# =====================================================================
# destiny_add_module() -- modular build engine
#
# Conventions: a module directory contains exactly these content dirs:
#   include/    public headers (external API) under include/destiny/<module path>/
#   src/        implementation + private headers: src/*.cpp compiled into the
#               library, src/*.hpp visible only inside the module
#   tests/      unit tests (one test exe per .cpp)
#   examples/   example programs (one exe per .cpp)
#   benchmarks/ benchmark programs (one exe per .cpp)
#   docs/       docs (incl. PLAN.md implementation plan)
# Module rule: a directory with CMakeLists.txt is a module (add_subdirectory'd).
# Naming: target = path relative to source/ joined with underscores (core_log);
#         public header prefix = destiny/<path>/ (#include "destiny/core/log/log.hpp");
#         namespace = destiny::<path> (namespace destiny::core::log).

# GTest: compiled from the vendored googletest source (thirdLib/googletest).
# This builds gtest with exactly the same compiler and stdlib as the project,
# so the ABI always matches. Avoids vcpkg's prebuilt MinGW gtest (whose
# libc++/pthread are incompatible with gcc/clang).
# add_subdirectory has built-in duplicate-load protection; call once globally.
add_subdirectory("${CMAKE_SOURCE_DIR}/thirdLib/googletest")
# =====================================================================

function(destiny_add_module)
  destiny_add_module_or_app("")
endfunction()

# Application module: builds an executable (apps applications), not a library.
# Shares all logic with destiny_add_module; only the target type differs.
function(destiny_add_application)
  destiny_add_module_or_app("EXECUTABLE")
endfunction()

function(destiny_add_module_or_app _dm_mode)
  # ---- 1. Module identity: path relative to source/ ----
  if(NOT DESTINY_SOURCE_ROOT)
    set(DESTINY_SOURCE_ROOT "${CMAKE_SOURCE_DIR}/source")
  endif()
  file(RELATIVE_PATH _dm_rel "${DESTINY_SOURCE_ROOT}" "${CMAKE_CURRENT_SOURCE_DIR}")
  if(_dm_rel STREQUAL ".")
    set(_dm_rel "")
  endif()
  # Path to target name: core/log -> core_log
  string(REPLACE "/" "_" _dm_target "${_dm_rel}")

  # ---- 2. Recursively discover submodules (direct subdirs with CMakeLists.txt) ----
  file(GLOB _dm_subdirs RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
       CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*/CMakeLists.txt")
  foreach(_dm_sub IN LISTS _dm_subdirs)
    get_filename_component(_dm_subdir "${_dm_sub}" DIRECTORY)
    add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/${_dm_subdir}")
  endforeach()

  # ---- Shape detection ----
  set(_dm_has_src FALSE)
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src")
    file(GLOB _dm_sources CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
    if(_dm_sources)
      set(_dm_has_src TRUE)
    endif()
  endif()
  file(GLOB _dm_children_targets CONFIGURE_DEPENDS
       "${CMAKE_CURRENT_SOURCE_DIR}/*/CMakeLists.txt")
  set(_dm_has_children FALSE)
  if(_dm_children_targets)
    set(_dm_has_children TRUE)
  endif()

  # ---- 3. Build target (per shape) ----
  if(_dm_has_src)
    if(_dm_mode STREQUAL "EXECUTABLE")
      # Application module: executable
      add_executable("${_dm_target}" ${_dm_sources})
      target_include_directories("${_dm_target}" PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include")
      target_include_directories("${_dm_target}" PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/src")
    else()
      # Real module: static library
      add_library("${_dm_target}" STATIC ${_dm_sources})
      # Public headers PUBLIC + private headers PRIVATE (visible only inside the
      # module, never propagated to consumers)
      target_include_directories("${_dm_target}" PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include")
      target_include_directories("${_dm_target}" PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/src")
    endif()
  elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/include")
    # Header-only module: INTERFACE library
    add_library("${_dm_target}" INTERFACE)
    target_include_directories("${_dm_target}" INTERFACE
      "${CMAKE_CURRENT_SOURCE_DIR}/include")
  elseif(_dm_has_children)
    # Container module: aggregate INTERFACE library linking all submodules
    add_library("${_dm_target}" INTERFACE)
    foreach(_dm_sub IN LISTS _dm_subdirs)
      get_filename_component(_dm_subdir "${_dm_sub}" DIRECTORY)
      string(REPLACE "/" "_" _dm_child "${_dm_rel}/${_dm_subdir}")
      string(REGEX REPLACE "^_" "" _dm_child "${_dm_child}")
      target_link_libraries("${_dm_target}" INTERFACE "${_dm_child}")
    endforeach()
  else()
    # Empty module: also build INTERFACE library so any dependant can link it
    add_library("${_dm_target}" INTERFACE)
  endif()

  # ---- 4. Tests: one test exe per tests/*.cpp ----
  if(DESTINY_BUILD_TESTS AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests")
    file(GLOB _dm_tests CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")
    foreach(_dm_test IN LISTS _dm_tests)
      get_filename_component(_dm_testname "${_dm_test}" NAME_WE)
      set(_dm_test_target "${_dm_target}_test_${_dm_testname}")
      add_executable("${_dm_test_target}" "${_dm_test}")
      target_link_libraries("${_dm_test_target}" PRIVATE
        "${_dm_target}" GTest::gtest_main GTest::gmock)
      add_test(NAME "${_dm_test_target}" COMMAND "${_dm_test_target}")
      # x86 build: copy runtime DLLs next to the exe (bin/), otherwise the
      # exe fails at runtime with 0xc000007b (libc++ not found)
      if(DESTINY_X86_RUNTIME_DLLS)
        foreach(_dm_dll IN LISTS DESTINY_X86_RUNTIME_DLLS)
          if(EXISTS "${_dm_dll}")
            add_custom_command(TARGET "${_dm_test_target}" POST_BUILD
              COMMAND "${CMAKE_COMMAND}" -E copy_if_different
                "${_dm_dll}" "${CMAKE_SOURCE_DIR}/bin/")
          endif()
        endforeach()
      endif()
    endforeach()
  endif()

  # ---- 5. Examples: one exe per examples/*.cpp ----
  if(DESTINY_BUILD_EXAMPLES AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/examples")
    file(GLOB _dm_examples CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/examples/*.cpp")
    foreach(_dm_ex IN LISTS _dm_examples)
      get_filename_component(_dm_exname "${_dm_ex}" NAME_WE)
      set(_dm_ex_target "${_dm_target}_example_${_dm_exname}")
      add_executable("${_dm_ex_target}" "${_dm_ex}")
      target_link_libraries("${_dm_ex_target}" PRIVATE "${_dm_target}")
    endforeach()
  endif()

  # ---- 6. Benchmarks: one exe per benchmarks/*.cpp ----
  if(DESTINY_BUILD_BENCHMARKS AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/benchmarks")
    file(GLOB _dm_bench CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/benchmarks/*.cpp")
    foreach(_dm_b IN LISTS _dm_bench)
      get_filename_component(_dm_bname "${_dm_b}" NAME_WE)
      set(_dm_b_target "${_dm_target}_bench_${_dm_bname}")
      add_executable("${_dm_b_target}" "${_dm_b}")
      target_link_libraries("${_dm_b_target}" PRIVATE "${_dm_target}")
    endforeach()
  endif()
endfunction()
