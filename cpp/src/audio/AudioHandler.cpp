//
// Created by JuanDGA on 5/19/25.
//

#include <thread>
#include <vector>
#include <ua_robotics/audio/AudioHandler.hpp>
#include <unitree/common/time/sleep.hpp>
#include <unitree/common/time/time_tool.hpp>

#include <ua_robotics/utils/audio/mix_audio.hpp>
#include <ua_robotics/utils/vector/vector_utils.hpp>
#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/g1/audio/g1_audio_client.hpp>

AudioHandler &AudioHandler::getInstance() {
    static AudioHandler instance;
    return instance;
}

AudioHandler::AudioHandler() {
    unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");
    std::thread player_thread(&AudioHandler::player, this);
    player_thread.detach();
}
AudioHandler::~AudioHandler() = default;

bool AudioHandler::add(const std::string &audio_path) {
    play_mutex.lock();
    if (audio_paths.count(audio_path)) {
        play_mutex.unlock();
        return false;
    }
    play_mutex.unlock();


    // Load the audio
    int32_t sample_rate = -1;
    int8_t num_channels = 0;
    bool isAudioFilePlayable = false;
    const std::vector<uint8_t> audio_data = read_audio(audio_path, &sample_rate, &num_channels, &isAudioFilePlayable);

    if (sample_rate != ALLOWED_SAMPLE_RATE || num_channels != ALLOWED_CHANNELS || !isAudioFilePlayable) {
        return false;
    }

    play_mutex.lock();
    audio_paths.insert(audio_path);
    play_mutex.unlock();

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
    std::unique_lock chunks_lock(play_mutex);

    while (!empty) {
        get_chunk(&chunk, &data, &empty, CHUNK_LENGTH);
        add_cv.wait(chunks_lock, [&] {
           return chunks_ready.count(audio_path) == 0;
        });
        chunks_to_play.push_back(chunk);
        chunks_ready.insert(audio_path);
        play_cv.notify_one();
    }
    add_cv.wait(chunks_lock, [&] {
       return chunks_ready.count(audio_path) == 0;
    });
    audio_paths.erase(audio_path);
    chunks_lock.unlock();
}

[[noreturn]] void AudioHandler::player() {
    unitree::robot::g1::AudioClient client;
    client.Init();
    client.SetVolume(100);
    std::unique_lock play_lock(play_mutex);
    std::vector<uint8_t> chunk_to_play;
    bool playing = false;
    while (true) {
        // Play current chunk
        if (!chunk_to_play.empty()) {
            playing = true;
            client.PlayStream("afdjudha", std::to_string(unitree::common::GetCurrentTimeMillisecond()), chunk_to_play);
        }
        const uint64_t start = unitree::common::GetCurrentTimeMicrosecond();
        chunk_to_play.clear();
        play_cv.wait(play_lock, [&] {
            return !audio_paths.empty() && chunks_ready.size() == audio_paths.size();
        });
        chunk_to_play = mix_audios(chunks_to_play);
        chunks_ready.clear();
        chunks_to_play.clear();
        const uint64_t elapsedTime = unitree::common::GetCurrentTimeMicrosecond() - start;
        const uint64_t to_sleep = 1'000'000 * DEFAULT_CHUNK_SECONDS_LENGTH - elapsedTime;
        if (playing) unitree::common::MicroSleep(to_sleep);
        playing = false;
        add_cv.notify_all();
    }
}