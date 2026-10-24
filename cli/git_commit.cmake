# Runs on every build (cli/CMakeLists.txt custom target) so an incremental rebuild never stamps an old commit (R-047, D-014).
execute_process(COMMAND git rev-parse HEAD WORKING_DIRECTORY "${SRC}" OUTPUT_VARIABLE commit OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
if(NOT commit)
    set(commit unknown)
endif()
file(WRITE "${OUT}.tmp" "#pragma once\n#define SINGVST_GIT_COMMIT \"${commit}\"\n")
execute_process(COMMAND ${CMAKE_COMMAND} -E copy_if_different "${OUT}.tmp" "${OUT}")
