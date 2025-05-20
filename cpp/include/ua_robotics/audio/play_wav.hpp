//
// Created by JuanDGA on 5/18/25.
//
#ifndef PLAY_WAV_HPP
#define PLAY_WAV_HPP
#include <string>
#include <vector>
#include <cstdint>

#define APP_NAME "wav_player"

constexpr int DEFAULT_VOLUME_VALUE = 70;
constexpr int DEFAULT_CHUNK_SECONDS_LENGTH = 4;
constexpr int ALLOWED_SAMPLE_RATE = 16000;
constexpr int ALLOWED_CHANNELS = 1;

std::vector<uint8_t> read_audio(const std::string &filename, int32_t *sampling_rate, int8_t *channelCount, bool *is_ok);

void play_audio(
  const std::string &net_interface,
  const std::string &audio_path,
  int volume = DEFAULT_VOLUME_VALUE,
  int chunk_seconds_length = DEFAULT_CHUNK_SECONDS_LENGTH
);

#endif //PLAY_WAV_HPP
