cmake_minimum_required(VERSION 3.31)
project(unitree_cpp_utilities)

set(CMAKE_CXX_STANDARD 17)
list(APPEND CMAKE_PREFIX_PATH "/opt/unitree_robotics")
find_package(unitree_sdk2 REQUIRED)

add_subdirectory(audio)

target_link_libraries(play_wav PRIVATE unitree_sdk2)
