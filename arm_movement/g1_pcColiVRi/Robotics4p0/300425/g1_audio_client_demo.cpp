#include <fstream>
#include <iostream>
#include <thread>
#include <unitree/common/time/time_tool.hpp>
#include <unitree/idl/ros2/String_.hpp>
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <unitree/robot/g1/audio/g1_audio_client.hpp>

#include "wav.hpp"

#define AUDIO_FILE_PATH "../example/g1/audio/test.wav"
#define AUDIO_SUBSCRIBE_TOPIC "rt/audio_msg"
#define GROUP_IP "239.168.123.161"
#define PORT 5555

#define WAV_SECOND 5
#define WAV_LEN (16000 * 2 * WAV_SECOND)
int sock;

void asr_handler(const void *msg) {
  std_msgs::msg::dds_::String_ *resMsg = (std_msgs::msg::dds_::String_ *)msg;
  std::cout << "Topic:\"rt/audio_msg\" recv: " << resMsg->data() << std::endl;
}

void thread_mic(void) {
  sock = socket(AF_INET, SOCK_DGRAM, 0);
  sockaddr_in local_addr{};
  local_addr.sin_family = AF_INET;
  local_addr.sin_port = htons(PORT);
  local_addr.sin_addr.s_addr = INADDR_ANY;
  bind(sock, (sockaddr *)&local_addr, sizeof(local_addr));

  ip_mreq mreq{};
  inet_pton(AF_INET, GROUP_IP, &mreq.imr_multiaddr);
  mreq.imr_interface.s_addr = INADDR_ANY;
  setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq));

  int total_bytes = 0;
  std::vector<int16_t> pcm_data;
  pcm_data.reserve(WAV_LEN / 2);

  std::cout << "start record!" << std::endl;
  while (total_bytes < WAV_LEN) {
    char buffer[2048];
    ssize_t len = recvfrom(sock, buffer, sizeof(buffer), 0, nullptr, nullptr);
    if (len > 0) {
      size_t sample_count = len / 2;
      const int16_t *samples = reinterpret_cast<const int16_t *>(buffer);
      pcm_data.insert(pcm_data.end(), samples, samples + sample_count);
      total_bytes += len;
    }
  }

  WriteWave("record.wav", 16000, pcm_data.data(), pcm_data.size(), 1);
  std::cout << "record finish! save to record.wav " << std::endl;
}

int main(int argc, char const *argv[]) {
  if (argc < 2) {
    std::cout << "Usage: audio_client_example [NetWorkInterface(eth0)]"
              << std::endl;
    exit(0);
  }
  int32_t ret;
  /*
   * Initilaize ChannelFactory
   */
  unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
  unitree::robot::g1::AudioClient client;
  client.Init();
  client.SetTimeout(10.0f);

  /*ASR message Example*/
  unitree::robot::ChannelSubscriber<std_msgs::msg::dds_::String_> subscriber(
      AUDIO_SUBSCRIBE_TOPIC);
  subscriber.InitChannel(asr_handler);

  /*Volume Example*/
  uint8_t volume;
  ret = client.GetVolume(volume);
  std::cout << "GetVolume API ret:" << ret
            << "  volume = " << std::to_string(volume) << std::endl;
  ret = client.SetVolume(100);
  std::cout << "SetVolume to 100% , API ret:" << ret << std::endl;

  // /*TTS Example*/
  // ret = client.TtsMaker("你好。我是宇树科技的机器人。例程启动成功",
  //                       0);  // Auto play
  // std::cout << "TtsMaker API ret:" << ret << std::endl;
  // unitree::common::Sleep(5);

  ret = client.TtsMaker(
      "Wellcome Hugo. Autogermana Innovation Manager. "
      "I'm G1. your smart robotic assistant. "
      "proudly working with the Autogermana team. ",
      1);  // Engilsh TTS
  std::cout << "TtsMaker API ret:" << ret << std::endl;
  unitree::common::Sleep(3);

  ret = client.TtsMaker(
      "At Autogermana. passion and innovation move us. "
      "just like BMW  MINI and BMW Motorrad inspire the world.",
      1);  // Engilsh TTS
  std::cout << "TtsMaker API ret:" << ret << std::endl;
  unitree::common::Sleep(3);

  ret = client.TtsMaker(
      "I'm here to support our incredible staff. "
      "guiding visitors. assisting at events. and delivering information. ",
      1);  // Engilsh TTS
  std::cout << "TtsMaker API ret:" << ret << std::endl;
  unitree::common::Sleep(3);

  ret = client.TtsMaker(
      "Together. we move emotions. and drive the future. ",
      1);  // Engilsh TTS
  std::cout << "TtsMaker API ret:" << ret << std::endl;
  unitree::common::Sleep(3);
  


  // /*Audio Play Example*/
  // int32_t sample_rate = 16000;
  // int8_t num_channels = 1;
  // bool filestate = true;
  // std::vector<uint8_t> pcm =
  //     ReadWave(AUDIO_FILE_PATH, &sample_rate, &num_channels, &filestate);

  // std::cout << "wav file sample_rate = " << sample_rate
  //           << " num_channels =  " << std::to_string(num_channels)
  //           << " filestate =" << filestate << std::endl;

  // if (true && sample_rate == 16000 && num_channels == 1) {
  //   client.PlayStream(
  //       "example", std::to_string(unitree::common::GetCurrentTimeMillisecond()),
  //       pcm);
  //   std::cout << "start play stream" << std::endl;
  //   unitree::common::Sleep(3);
  //   std::cout << "stop play stream" << std::endl;
  //   ret = client.PlayStop("example");
  // } else {
  //   std::cout << "audio file format error, please check!" << std::endl;
  // }

  // /*LED Control Example*/
  // client.LedControl(0, 255, 0);
  // unitree::common::Sleep(1);
  // client.LedControl(0, 0, 0);
  // unitree::common::Sleep(1);
  // client.LedControl(0, 0, 255);

  std::cout << "AudioClient api test finish , asr start..." << std::endl;

  std::thread mic_t(thread_mic);

  while (1) {
    sleep(1);  // wait for asr message
  }
  mic_t.join();
  return 0;
}