//
// Created by JuanDGA on 5/19/25.
//
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <ua_robotics/messages/SimpleMessage.hpp>
#include <ua_robotics/audio/AudioHandler.hpp>


void Handler(const void* msg) {
    const auto* message = static_cast<const SimpleMessage::Msg *>(msg);
    std::cout << "Starting " << message->message() << std::endl;
    play_audio("eth0", message->message(), 90, 6);
}


int main() {
    unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");
    unitree::robot::ChannelSubscriber<SimpleMessage::Msg> subscriber("AUDIO_PATHS");
    subscriber.InitChannel(Handler);
    std::string input;
    while (true) {
        unitree::common::Sleep(10);
    }
    subscriber.CloseChannel();
}