add_executable(play_wav play_wav_executable.cpp)
add_executable(audio_service_node audio_service_node.cpp
        ../include/ua_robotics/utils/cli/args_parser.h)
add_executable(play_wav_request play_wav_request.cpp)

target_link_libraries(play_wav PRIVATE ua_robotics)
target_link_libraries(audio_service_node PRIVATE ua_robotics)
target_link_libraries(play_wav_request PRIVATE ua_robotics)
