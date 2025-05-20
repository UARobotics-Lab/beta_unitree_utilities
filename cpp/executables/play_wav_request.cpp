//
// Created by JuanDGA on 5/20/25.
//
#include <unitree/robot/channel/channel_publisher.hpp>
#include <ua_robotics/messages/SimpleMessage.hpp>
#include <ua_robotics/utils/cli/args_parser.h>

using namespace unitree::robot;
using namespace unitree::common;

void print_usage() {
    std::cout << "Usage: play_wav_request --if=<wav_file_path>\n";
    std::cout << "  --if                Required. Absolute path to .wav file\n";
    std::cout << std::endl;
}

int main(const int argc, char const *argv[]) {
    ChannelFactory::Instance()->Init(0, "eth0");
    ChannelPublisher<SimpleMessage::Msg> publisher("AUDIO_PATHS");
    std::map<std::string, std::string> args = parse_named_args(argc, argv, 1, print_usage);
    if (args.find("if") == args.end()) {
        std::cerr << "Error: Missing required argument --if=<wav_file_path>\n";
        print_usage();
        exit(1);
    }
    publisher.InitChannel();
    const SimpleMessage::Msg msg(1, args["if"]);
    publisher.Write(msg);
}