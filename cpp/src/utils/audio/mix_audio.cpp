//
// Created by JuanDGA on 5/20/25.
//
#include <algorithm>
#include <ua_robotics/utils/audio/mix_audio.hpp>
std::vector<uint8_t> mix_audios(const std::vector<std::vector<uint8_t>> &audios) {
    // Find the length of the longest audio chunk
    size_t max_size = 0;
    for (const auto &audio : audios) {
        if (audio.size() > max_size) {
            max_size = audio.size();
        }
    }

    // Create result audio with the same size
    std::vector<uint8_t> result_audio(max_size);

    // Process two bytes at a time since each sample is 16-bit (2 bytes)
    for (size_t i = 0; i < max_size; i += 2) {
        // Skip if we can't get a complete sample (need 2 bytes)
        if (i + 1 >= max_size) continue;

        int32_t mixed_sample = 0;
        int sample_count = 0;

        // Mix samples from all audio chunks
        for (const auto &audio : audios) {
            // Only process if this audio has enough data
            if (i + 1 < audio.size()) {
                // Convert two bytes to a 16-bit sample (little-endian)
                int16_t sample = static_cast<int16_t>(audio[i]) |
                                (static_cast<int16_t>(audio[i + 1]) << 8);
                mixed_sample += sample;
                sample_count++;
            }
        }

        // Average the samples if we have more than one
        if (sample_count > 1) {
            mixed_sample /= sample_count;
        }

        // Clamp to 16-bit range
        mixed_sample = std::min<int32_t>(std::max<int32_t>(mixed_sample, INT16_MIN), INT16_MAX);

        // Convert back to bytes (little-endian)
        result_audio[i] = mixed_sample & 0xFF;
        result_audio[i + 1] = (mixed_sample >> 8) & 0xFF;
    }

    return result_audio;
}