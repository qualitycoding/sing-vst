# Pinned third-party code (plan/ENVIRONMENT.md; hashes from research/spikes/deps-pins/output.txt and C-014).
include(FetchContent)
find_package(Threads REQUIRED)

# nlohmann/json 3.12.0, MIT (C-049)
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
    URL_HASH SHA256=42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa)
FetchContent_MakeAvailable(json)

# ONNX Runtime 1.31.0 prebuilt CPU package (D-002). Headers only at compile time; the library is loaded by path (D-024).
set(SINGVST_ORT_VERSION 1.31.0)
if(WIN32)
    set(_ort_pkg onnxruntime-win-x64-${SINGVST_ORT_VERSION}.zip)
    set(_ort_sha 3958d8a44984160692c1b4ffd0de3cb48f8c39f9d34bb31e433db06e30b82195)
    set(_ort_lib_name onnxruntime.dll)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(_ort_pkg onnxruntime-linux-x64-${SINGVST_ORT_VERSION}.tgz)
    set(_ort_sha cc5c72baf5ae5c8238a6841f0897227be2d02826b9cf98eaf02fdefaeeb03a57)
    set(_ort_lib_name libonnxruntime.so.${SINGVST_ORT_VERSION})
else()
    message(FATAL_ERROR "Unsupported platform: Windows x64 and Linux x64 only (A-008)")
endif()
if(SINGVST_ORT_DIR)
    set(_ort_root ${SINGVST_ORT_DIR})
else()
    FetchContent_Declare(ort URL https://github.com/microsoft/onnxruntime/releases/download/v${SINGVST_ORT_VERSION}/${_ort_pkg}
        URL_HASH SHA256=${_ort_sha})
    FetchContent_MakeAvailable(ort)
    set(_ort_root ${ort_SOURCE_DIR})
endif()
set(SINGVST_ORT_INCLUDE_DIR ${_ort_root}/include CACHE INTERNAL "")
set(SINGVST_ORT_LIBRARY ${_ort_root}/lib/${_ort_lib_name} CACHE INTERNAL "")
set(SINGVST_ORT_LICENSE ${_ort_root}/LICENSE CACHE INTERNAL "")
if(NOT EXISTS ${SINGVST_ORT_INCLUDE_DIR}/onnxruntime_cxx_api.h OR NOT EXISTS ${SINGVST_ORT_LIBRARY})
    message(FATAL_ERROR "ONNX Runtime ${SINGVST_ORT_VERSION} not found under ${_ort_root}")
endif()
set(SINGVST_CMUDICT ${PROJECT_SOURCE_DIR}/third_party/cmudict/cmudict.dict CACHE INTERNAL "")

# Copies the runtime files a binary loads by path (ONNX Runtime library + licence, CMUdict) into a directory after build.
function(singvst_copy_runtime_files target dir)
    add_custom_command(TARGET ${target} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${dir}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${SINGVST_ORT_LIBRARY}" "${SINGVST_CMUDICT}" "${dir}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${SINGVST_ORT_LICENSE}" "${dir}/onnxruntime-LICENSE.txt"
        VERBATIM)
endfunction()

if(SINGVST_BUILD_TESTS)
    FetchContent_Declare(Catch2 GIT_REPOSITORY https://github.com/catchorg/Catch2.git GIT_TAG v3.16.1 GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(Catch2)
endif()
if(SINGVST_BUILD_PLUGIN)
    FetchContent_Declare(JUCE GIT_REPOSITORY https://github.com/juce-framework/JUCE.git GIT_TAG 9.0.3 GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(JUCE)
endif()
