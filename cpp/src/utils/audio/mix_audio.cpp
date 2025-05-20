//
// Created by JuanDGA on 5/20/25.
//
#include <algorithm>
#include <ua_robotics/utils/audio/mix_audio.hpp>

std::vector<uint8_t> mix_audios(const std::vector<std::vector<uint8_t>> &audios) {
    size_t size = 0;
    for (const auto &audio : audios) {
        if (audio.size() > size) size = audio.size();
    }

    std::vector<uint8_t> result_audio;

    for (int i = 0; i < size; ++i) {
        int value = 0;
        for (int j = 0; j < audios.size(); ++j) {
            auto audio = audios[j];
            if (audio.size() > i) {
                value += static_cast<int>(audio[i]) - 128;
            }
        }
        value += 128;
        value = std::min(std::max(value, 0), 255);
        result_audio.push_back(value);
    }

    return result_audio;
}