//
// Created by JuanDGA on 5/19/25.
//
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <ua_robotics/messages/SimpleMessage.hpp>


void Handler(const void* msg) {

}


int main() {
    unitree::robot::ChannelFactory::Instance()->Init(0);
    unitree::robot::ChannelSubscriber<SimpleMessage::Msg> subscriber("AUDIO_PATHS");
    subscriber.InitChannel(Handler);
    std::string input;
    std::cout << "Press enter to close the service\n> ";
    std::getline(std::cin, input);
    subscriber.CloseChannel();
}