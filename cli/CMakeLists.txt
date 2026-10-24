# singvst-render (D-014)
set(SINGVST_GIT_HEADER ${CMAKE_CURRENT_BINARY_DIR}/generated/singvst_git_commit.h)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/generated)
add_custom_target(singvst_git_commit
    COMMAND ${CMAKE_COMMAND} -DSRC=${PROJECT_SOURCE_DIR} -DOUT=${SINGVST_GIT_HEADER} -P ${CMAKE_CURRENT_SOURCE_DIR}/git_commit.cmake
    BYPRODUCTS ${SINGVST_GIT_HEADER} COMMENT "Stamping the git commit" VERBATIM)
add_executable(singvst-render main.cpp)
add_dependencies(singvst-render singvst_git_commit)
target_include_directories(singvst-render PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/generated ${PROJECT_SOURCE_DIR}/core/src)
target_link_libraries(singvst-render PRIVATE singvst_core nlohmann_json::nlohmann_json)
target_compile_definitions(singvst-render PRIVATE SINGVST_ORT_VERSION="${SINGVST_ORT_VERSION}")
singvst_copy_runtime_files(singvst-render $<TARGET_FILE_DIR:singvst-render>)
