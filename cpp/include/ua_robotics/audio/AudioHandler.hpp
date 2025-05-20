//
// Created by JuanDGA on 5/19/25.
//
#ifndef AUDIOHANDLER_HPP
#define AUDIOHANDLER_HPP
#include <condition_variable>
#include <mutex>
#include <string>
#include <unordered_set>
#include "play_wav.hpp"

constexpr uint64_t CHUNK_LENGTH = DEFAULT_CHUNK_SECONDS_LENGTH * ALLOWED_SAMPLE_RATE * 2;

class AudioHandler {
public:
    static AudioHandler& getInstance();
    bool add(const std::string& audio_path);
    bool remove(const std::string& audio_path);

    // --- Singleton Management ---
    AudioHandler(const AudioHandler&) = delete;
    AudioHandler& operator=(const AudioHandler&) = delete;

    AudioHandler(AudioHandler&&) = delete;
    AudioHandler& operator=(AudioHandler&&) = delete;

private:
    AudioHandler();
    ~AudioHandler();

    void chunk_processor(const std::string &audio_path, std::vector<uint8_t> data);
    [[noreturn]] void player();

    std::mutex play_mutex;
    std::condition_variable play_cv;
    std::condition_variable add_cv;

    std::unordered_set<std::string> audio_paths;
    std::vector<std::vector<uint8_t>> chunks_to_play;
    std::unordered_set<std::string> chunks_ready;
};

#endif //AUDIOHANDLER_HPP