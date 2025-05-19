file(GLOB_RECURSE UA_ROBOTICS_SRC CONFIGURE_DEPENDS
        ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp
)

add_library(ua_robotics STATIC ${UA_ROBOTICS_SRC})

target_include_directories(ua_robotics PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(ua_robotics PUBLIC unitree_sdk2)