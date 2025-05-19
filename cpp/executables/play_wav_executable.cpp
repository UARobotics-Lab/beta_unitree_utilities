//
// Created by JuanDGA on 5/17/25.
//
#include <iostream>
#include <map>
#include <string>
#include <ua_robotics/audio/play_wav.hpp>


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

  play_audio(interface, audio_path, volume, chunk_seconds_length);
  return EXIT_SUCCESS;
}