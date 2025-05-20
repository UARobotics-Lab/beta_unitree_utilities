//
// Created by JuanDGA on 5/20/25.
//
#include <unitree/robot/channel/channel_publisher.hpp>
#include <ua_robotics/messages/SimpleMessage.hpp>

using namespace unitree::robot;
using namespace unitree::common;

int main() {
    ChannelFactory::Instance()->Init(0);
    ChannelPublisher<SimpleMessage::Msg> publisher("AUDIO_PATHS");

    publisher.InitChannel();
    SimpleMessage::Msg msg(unitree::common::GetCurrentTimeMillisecond(), "/home/juanguevara/output.wav");
    publisher.Write(msg);
}