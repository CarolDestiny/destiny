# =====================================================================
# destiny_add_module() —— 模块化构建引擎
#   include/  公开头（对外 API）   —— 放在 include/destiny/<模块路径>/ 下
#   src/      实现源码 + 私有头     —— src/*.cpp 编译进库，src/*.hpp 仅供模块内部
#   tests/    单元测试（每个 .cpp 一个测试 exe）
#   examples/ 样例程序（每个 .cpp 一个 exe）
#   benchmarks/ 跑分程序（每个 .cpp 一个 exe）
#   docs/     文档（含 PLAN.md 实现计划）
# 模块判定：目录里有 CMakeLists.txt 即视为模块（本宏会 add_subdirectory 它）。
# 命名约定：target = 相对 source/ 的路径用下划线拼接（如 core_log）；
#           公开头 include 前缀 = destiny/<路径>/（如 #include "destiny/core/log/log.hpp"）；
#           命名空间 = destiny::<路径>（如 namespace destiny::core::log）。

# GTest：用项目自带的 googletest 源码编译（thirdLib/googletest）。
# 这样 gtest 与项目使用完全相同的编译器和标准库，ABI 必然匹配。
# 不依赖 vcpkg 的 MinGW 预编译 gtest（其 libc++/pthread 与 gcc/clang 不兼容）。
# add_subdirectory 自带防重复加载保护，此处调用一次全局生效。
add_subdirectory("${CMAKE_SOURCE_DIR}/thirdLib/googletest")
# =====================================================================

function(destiny_add_module)
  # ---- ① 模块身份：相对 source/ 的路径 ----
  if(NOT DESTINY_SOURCE_ROOT)
    set(DESTINY_SOURCE_ROOT "${CMAKE_SOURCE_DIR}/source")
  endif()
  file(RELATIVE_PATH _dm_rel "${DESTINY_SOURCE_ROOT}" "${CMAKE_CURRENT_SOURCE_DIR}")
  if(_dm_rel STREQUAL ".")
    set(_dm_rel "")
  endif()
  # 路径转 target 名：core/log -> core_log
  string(REPLACE "/" "_" _dm_target "${_dm_rel}")

  # ---- ② 递归发现子模块（直接子目录中含 CMakeLists.txt 的）----
  file(GLOB _dm_subdirs RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
       CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*/CMakeLists.txt")
  foreach(_dm_sub IN LISTS _dm_subdirs)
    get_filename_component(_dm_subdir "${_dm_sub}" DIRECTORY)
    add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/${_dm_subdir}")
  endforeach()

  # ---- 形态判定 ----
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

  # ---- ③ 建库目标（按形态分流）----
  if(_dm_has_src)
    # 实模块：静态库
    add_library("${_dm_target}" STATIC ${_dm_sources})
    # 公开头 PUBLIC + 私有头 PRIVATE（只对本模块内部可见，不传给消费者）
    target_include_directories("${_dm_target}" PUBLIC
      "${CMAKE_CURRENT_SOURCE_DIR}/include")
    target_include_directories("${_dm_target}" PRIVATE
      "${CMAKE_CURRENT_SOURCE_DIR}/src")
  elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/include")
    # 纯头模块：INTERFACE 库
    add_library("${_dm_target}" INTERFACE)
    target_include_directories("${_dm_target}" INTERFACE
      "${CMAKE_CURRENT_SOURCE_DIR}/include")
  elseif(_dm_has_children)
    # 容器模块：聚合 INTERFACE 库，链接全部子模块
    add_library("${_dm_target}" INTERFACE)
    foreach(_dm_sub IN LISTS _dm_subdirs)
      get_filename_component(_dm_subdir "${_dm_sub}" DIRECTORY)
      string(REPLACE "/" "_" _dm_child "${_dm_rel}/${_dm_subdir}")
      string(REGEX REPLACE "^_" "" _dm_child "${_dm_child}")
      target_link_libraries("${_dm_target}" INTERFACE "${_dm_child}")
    endforeach()
  else()
    # 空模块：也建 INTERFACE 库，保证任何依赖方都能链接它
    add_library("${_dm_target}" INTERFACE)
  endif()

  # ---- ④ 测试：每个 tests/*.cpp 一个测试 exe ----
  if(DESTINY_BUILD_TESTS AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests")
    file(GLOB _dm_tests CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")
    foreach(_dm_test IN LISTS _dm_tests)
      get_filename_component(_dm_testname "${_dm_test}" NAME_WE)
      set(_dm_test_target "${_dm_target}_test_${_dm_testname}")
      add_executable("${_dm_test_target}" "${_dm_test}")
      target_link_libraries("${_dm_test_target}" PRIVATE
        "${_dm_target}" GTest::gtest_main GTest::gmock)
      add_test(NAME "${_dm_test_target}" COMMAND "${_dm_test_target}")
      # x86 构建：把运行时 DLL 复制到 exe 旁（bin/），否则运行时找不到 libc++ 报 0xc000007b
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

  # ---- ⑤ 样例：每个 examples/*.cpp 一个 exe ----
  if(DESTINY_BUILD_EXAMPLES AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/examples")
    file(GLOB _dm_examples CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/examples/*.cpp")
    foreach(_dm_ex IN LISTS _dm_examples)
      get_filename_component(_dm_exname "${_dm_ex}" NAME_WE)
      set(_dm_ex_target "${_dm_target}_example_${_dm_exname}")
      add_executable("${_dm_ex_target}" "${_dm_ex}")
      target_link_libraries("${_dm_ex_target}" PRIVATE "${_dm_target}")
    endforeach()
  endif()

  # ---- ⑥ 跑分：每个 benchmarks/*.cpp 一个 exe ----
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
