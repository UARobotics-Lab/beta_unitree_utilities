//
// Created by JuanDGA on 5/19/25.
//

#include <thread>
#include <vector>
#include <ua_robotics/audio/AudioHandler.hpp>
#include <unitree/common/time/sleep.hpp>
#include <unitree/common/time/time_tool.hpp>

#include "ua_robotics/utils/vector/vector_utils.hpp"

AudioHandler &AudioHandler::getInstance() {
    static AudioHandler instance;
    return instance;
}

AudioHandler::AudioHandler() {
    std::thread player_thread(&AudioHandler::player, this);
    player_thread.detach();
}
AudioHandler::~AudioHandler() { }

bool AudioHandler::add(const std::string &audio_path) {
    std::cout << "Trying to add " << audio_path << std::endl;
    std::vector<uint8_t> audioData;
    paths_mtx.lock();
    if (audio_paths.count(audio_path)) {
        paths_mtx.unlock();
        return false;
    }
    paths_mtx.unlock();
    std::cout << "Trying to load " << audio_path << std::endl;


    // Load the audio
    int32_t sample_rate = -1;
    int8_t num_channels = 0;
    bool isAudioFilePlayable = false;
    const std::vector<uint8_t> audio_data = read_audio(audio_path, &sample_rate, &num_channels, &isAudioFilePlayable);

    if (sample_rate != ALLOWED_SAMPLE_RATE || num_channels != ALLOWED_CHANNELS || !isAudioFilePlayable) {
        return false;
    }

    std::cout << "Loaded " << audio_path << std::endl;

    paths_mtx.lock();
    audio_paths.insert(audio_path);
    paths_mtx.unlock();

    std::thread chunk_processor_thread(&AudioHandler::chunk_processor, this, audio_path, audio_data);
    chunk_processor_thread.detach();

    return true;
}

bool AudioHandler::remove(const std::string &audio_path) {
    return true;
}


void AudioHandler::chunk_processor(const std::string &audio_path, std::vector<uint8_t> data) {
    bool empty = false;
    std::vector<uint8_t> chunk;
    std::cout << "Started chunks from " << audio_path << std::endl;

    while (!empty) {
        get_chunk(&chunk, &data, &empty, chunk_length);
        while (true) {
            chunks_mtx.lock();
            if (chunks_ready.count(audio_path)) {
                chunks_mtx.unlock();
            } else {
                break;
            }
        }
        chunks_to_play.push_back(chunk);
        chunks_ready.insert(audio_path);
        std::cout << "Added chunk from " << audio_path << std::endl;
        chunks_mtx.unlock();
    }
    paths_mtx.lock();
    audio_paths.erase(audio_path);
    std::cout << "Finished chunks from " << audio_path << std::endl;
    paths_mtx.unlock();
}

void AudioHandler::player() {
    std::cout << "Processor initialized " << std::endl;
    while (true) {
        paths_mtx.lock();
        chunks_mtx.lock();
        if (chunks_ready.size() < audio_paths.size() || audio_paths.size() == 0) {
            chunks_mtx.unlock();
            paths_mtx.unlock();
        } else {
            paths_mtx.unlock();
            break;
        }
    }
    std::cout << "First mixed chunk loaded" << std::endl;
    chunks_mtx.unlock();
    while (true) {
        // Play current chunk
        std::cout << "Playing chunk" << std::endl;
        const uint64_t start = unitree::common::GetCurrentTimeMicrosecond();

        while (true) {
            paths_mtx.lock();
            chunks_mtx.lock();
            if (chunks_ready.size() < audio_paths.size() || audio_paths.size() == 0) {
                chunks_mtx.unlock();
                paths_mtx.unlock();
            } else {
                paths_mtx.unlock();
                break;
            }
        }
        // Mix audios

        chunks_ready.clear();
        chunks_to_play.clear();
        const uint64_t elapsedTime = unitree::common::GetCurrentTimeMicrosecond() - start;
        const uint64_t to_sleep = 1000000 * chunk_length - elapsedTime;
        unitree::common::MicroSleep(to_sleep);
        chunks_mtx.unlock();
    }
}