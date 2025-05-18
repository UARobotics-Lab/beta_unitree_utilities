//
// Created by JuanDGA on 5/16/25.
//
#include <fstream>
#include <iostream>
#include <unitree/common/time/time_tool.hpp>
#include <unitree/robot/g1/audio/g1_audio_client.hpp>

#include "../utils/audio/wav.hpp"
#include "../utils/vector/vector_utils.hpp"

#define APP_NAME "wav_player"
#define DEFAULT_VOLUME_VALUE 70
#define DEFAULT_CHUNK_SECONDS_LENGTH 4

/**
 * Generates a unique identifier based on the current time in milliseconds.
 *
 * @return A string representation of the current time in milliseconds, used as id.
 */
std::string next_id() {
  return std::to_string(unitree::common::GetCurrentTimeMillisecond());
}

/**
 * Sets the volume of the audio system to the specified target value.
 *
 * @param target The desired volume level, represented as an integer percentage (0-100).
 * @param client The AudioClient instance used to communicate with the audio system.
 */
void set_volume(const int target, unitree::robot::g1::AudioClient client) {
  client.SetVolume(target);
  std::cout << "Volume set to " << target << "%" << std::endl;
}

/**
 * Reads an audio file and returns its data as a reversed vector of bytes.
 * The function reads a WAVE file, extracts audio data along with metadata
 * such as sampling rate, channel count, and file status, then reverses the audio data.
 *
 * @param filename The name of the audio file to be read.
 * @param sampling_rate Pointer to an integer to store the sampling rate of the audio.
 * @param channelCount Pointer to an integer to store the number of channels in the audio.
 * @param is_ok Pointer to a boolean that will be set to true if the file is successfully read, otherwise false.
 *
 * @return A vector of bytes containing the reversed audio data from the file.
 */
std::vector<uint8_t> read_audio(const std::string &filename, int32_t *sampling_rate, int8_t *channelCount, bool *is_ok) {
  std::vector<uint8_t> result = ReadWave(filename, sampling_rate, channelCount, is_ok);
  std::reverse(result.begin(), result.end());
  return result;
}

/**
 * Plays an audio file over a specified network interface, using chunked streaming.
 * The audio file must be a mono-channel 16 kHz WAV file, otherwise an error will be displayed.
 *
 * @param net_interface A pointer to the network interface used for streaming audio.
 * @param audio_path The file path of the audio file to be played.
 * @param volume The target volume level to be set during playback (percentage).
 * @param chunk_seconds_length The duration (in seconds) for each audio chunk to be streamed.
 */
void play_audio(const std::string *net_interface, const std::string &audio_path, const int volume, const int chunk_seconds_length) {
  unitree::robot::ChannelFactory::Instance()->Init(0, *net_interface);
  unitree::robot::g1::AudioClient client;
  client.Init();

  set_volume(volume, client);

  int32_t sample_rate = -1;
  int8_t num_channels = 0;
  bool isAudioFilePlayable = false;

  std::vector<uint8_t> audio_data = read_audio(audio_path, &sample_rate, &num_channels, &isAudioFilePlayable);

  std::cout << "wav file sample_rate = " << sample_rate
            << " num_channels =  " << std::to_string(num_channels)
            << " isAudioFilePlayable =" << isAudioFilePlayable << std::endl;

  const int chunk_length = chunk_seconds_length * 16000 * 2;

  if (isAudioFilePlayable && sample_rate == 16000 && num_channels == 1) {
    std::vector<uint8_t> chunk;

    bool empty = false;
    get_chunk(&chunk, &audio_data, &empty, chunk_length);

    while (!empty) {
      client.PlayStream(APP_NAME, next_id(), chunk);
      const uint64_t start = unitree::common::GetCurrentTimeMicrosecond();
      get_chunk(&chunk, &audio_data, &empty, chunk_length);
      const uint64_t elapsedTime = unitree::common::GetCurrentTimeMicrosecond() - start;
      const uint64_t to_sleep = 1000000 * chunk_length - elapsedTime;
      unitree::common::MicroSleep(to_sleep);
    }
  } else {
    std::cout << "audio file format error, please check!" << std::endl;
  }
}

void print_usage() {
  std::cout << "Usage: play_wav <interface> --if=<wav_file_path> [--volume=<0-100>] [--chunk-duration=<4-100>]\n";
  std::cout << "  <interface>         Required. Network interface (e.g., eth0)\n";
  std::cout << "  --if                Required. Absolute path to .wav file\n";
  std::cout << "  --volume            Optional. Playback volume [0-100] (default: " << DEFAULT_VOLUME_VALUE << ")\n";
  std::cout << "  --chunk-duration    Optional. Audio chunk duration in seconds [4-100] (default: " << DEFAULT_CHUNK_SECONDS_LENGTH << ")\n";
  std::cout << std::endl;
}

std::map<std::string, std::string> parse_named_args(const int argc, char const *argv[], const int start_index) {
  std::map<std::string, std::string> args;

  for (int i = start_index; i < argc; ++i) {
    std::string arg(argv[i]);
    const size_t pos = arg.find('=');
    if (arg.substr(0, 2) != "--" || pos == std::string::npos) {
      std::cerr << "Unknown or malformed argument: " << arg << "\n";
      print_usage();
      exit(1);
    }
    std::string key = arg.substr(2, pos - 2);
    const std::string value = arg.substr(pos + 1);
    args[key] = value;
  }

  return args;
}

void get_execution_params(const int argc, char const *argv[], std::string *arg_network_interface, std::string *arg_audio_path, int *arg_volume, int *arg_chunk_seconds_length) {
  if (argc < 3) {
    std::cerr << "Error: Missing required arguments.\n";
    print_usage();
    exit(1);
  }

  const std::string network_interface = argv[1];
  std::map<std::string, std::string> args = parse_named_args(argc, argv, 2);

  if (args.find("if") == args.end()) {
    std::cerr << "Error: Missing required argument --if=<wav_file_path>\n";
    print_usage();
    exit(1);
  }

  const std::string wav_file_path = args["if"];

  int volume = DEFAULT_VOLUME_VALUE;
  if (args.find("volume") != args.end()) {
    try {
      volume = std::stoi(args["volume"]);
      volume = std::min(100, std::max(4, volume));
    } catch (...) {
      std::cerr << "Warning: Invalid volume value. Using default " << DEFAULT_VOLUME_VALUE << "\n";
    }
  }

  int chunk_duration = DEFAULT_CHUNK_SECONDS_LENGTH;
  if (args.find("chunk-duration") != args.end()) {
    try {
      chunk_duration = std::stoi(args["chunk-duration"]);
      chunk_duration = std::min(100, std::max(4, chunk_duration));
    } catch (...) {
      std::cerr << "Warning: Invalid chunk duration. Using default " << DEFAULT_CHUNK_SECONDS_LENGTH << "\n";
    }
  }


  *arg_network_interface = network_interface;
  *arg_audio_path = wav_file_path;
  *arg_volume = volume;
  *arg_chunk_seconds_length = chunk_duration;
}

int main(const int argc, char const *argv[]) {
  std::string interface;
  std::string audio_path;
  int volume;
  int chunk_seconds_length;
  get_execution_params(argc, argv, &interface, &audio_path, &volume, &chunk_seconds_length);

  play_audio(&interface, audio_path, volume, chunk_seconds_length);
  return 0;
}