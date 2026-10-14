# singvst_core: JUCE-free library (D-001). Links nothing from ONNX Runtime (D-024).
file(GLOB SINGVST_CORE_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
add_library(singvst_core STATIC ${SINGVST_CORE_SOURCES})
target_include_directories(singvst_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include PRIVATE ${SINGVST_ORT_INCLUDE_DIR})
target_compile_definitions(singvst_core PRIVATE ORT_API_MANUAL_INIT SINGVST_ORT_VERSION="${SINGVST_ORT_VERSION}")
target_link_libraries(singvst_core PRIVATE nlohmann_json::nlohmann_json PUBLIC Threads::Threads ${CMAKE_DL_LIBS})
