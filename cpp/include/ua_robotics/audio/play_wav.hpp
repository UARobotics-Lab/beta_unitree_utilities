//
// Created by JuanDGA on 5/18/25.
//
#ifndef PLAY_WAV_HPP
#define PLAY_WAV_HPP
#include <string>

#define DEFAULT_VOLUME_VALUE 70
#define DEFAULT_CHUNK_SECONDS_LENGTH 4

void play_audio(
  const std::string &net_interface,
  const std::string &audio_path,
  int volume = DEFAULT_VOLUME_VALUE,
  int chunk_seconds_length = DEFAULT_CHUNK_SECONDS_LENGTH
);

#endif //PLAY_WAV_HPP
