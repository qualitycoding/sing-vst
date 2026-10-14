# JUCE 9.0.3 instrument (D-001, D-010, D-022, D-027). Runtime files sit beside each binary (D-024).
juce_add_plugin(SingVst
    COMPANY_NAME "qualitycoding"
    PLUGIN_MANUFACTURER_CODE Qcod
    PLUGIN_CODE Sngv
    FORMATS VST3 Standalone
    PRODUCT_NAME "Sing VST"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS TRUE
    VST3_CATEGORIES Instrument Synth
    COPY_PLUGIN_AFTER_BUILD FALSE)
file(GLOB SINGVST_PLUGIN_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp)
target_sources(SingVst PRIVATE ${SINGVST_PLUGIN_SOURCES})
target_include_directories(SingVst PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(SingVst PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0 JUCE_STRICT_REFCOUNTEDPOINTER=1
    JUCE_MODAL_LOOPS_PERMITTED=1)   # tests pump the message loop with runDispatchLoopUntil (T-054..T-058)
target_link_libraries(SingVst
    PUBLIC singvst_core juce::juce_audio_utils
           juce::juce_recommended_config_flags juce::juce_recommended_lto_flags juce::juce_recommended_warning_flags)
singvst_copy_runtime_files(SingVst_VST3 $<TARGET_FILE_DIR:SingVst_VST3>)
singvst_copy_runtime_files(SingVst_Standalone $<TARGET_FILE_DIR:SingVst_Standalone>)
