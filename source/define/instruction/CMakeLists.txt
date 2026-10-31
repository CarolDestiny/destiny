add_library(destiny_define_instruction INTERFACE)

target_include_directories(
        destiny_define_instruction
        INTERFACE
        $<BUILD_INTERFACE:${DESTINY_INCLUDE_ROOT}>
)

destiny_map_headers(
        destiny_define_instruction
        "define/instruction"
        instruction.hpp
)
