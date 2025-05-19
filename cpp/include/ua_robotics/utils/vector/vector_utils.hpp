//
// Created by JuanDGA on 5/17/25.
//

#ifndef VECTOR_UTILS_HPP
#define VECTOR_UTILS_HPP
#include <algorithm>
#include <vector>


/**
 * Extracts a chunk of audio data from the source buffer and places it in the
 * target buffer. Clears the target buffer before adding data and removes the
 * processed chunk from the source buffer.
 *
 * @param target Pointer to the target vector where the extracted chunk will be stored.
 * @param source Pointer to the source vector containing audio data.
 * @param is_empty Pointer to a boolean indicating whether the source buffer becomes empty or was already empty.
 * @param chunk_length The length of the chunk to extract.
 */
template <typename T>
void get_chunk(std::vector<T> *target, std::vector<T> *source, bool *is_empty, const int chunk_length) {
    if (!target || !source || !is_empty || chunk_length <= 0) {
        if (!target) throw std::invalid_argument("The 'target' pointer cannot be null");
        if (!source) throw std::invalid_argument("The 'source' pointer cannot be null");
        if (!is_empty) throw std::invalid_argument("The 'is_empty' pointer cannot be null");
        throw std::invalid_argument("Chunk length must be greater than 0");
    }

    target->clear();

    if (source->empty()) {
        *is_empty = true;
        return;
    }

    *is_empty = false;

    const size_t to_remove = std::min(static_cast<size_t>(chunk_length), source->size());

    for (int i = 0; i < to_remove; i++) {
        target->push_back(source->at(source->size() - 1));
        source->pop_back();
    }
}

#endif //VECTOR_UTILS_HPP
