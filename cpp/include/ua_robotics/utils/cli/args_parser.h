//
// Created by juanguevara on 5/20/25.
//

#ifndef ARGS_PARSER_H
#define ARGS_PARSER_H
#include <iostream>
#include <map>
#include <string>

inline std::map<std::string, std::string> parse_named_args(const int argc, char const *argv[], const int start_index, void (*print_usage)()) {
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
#endif //ARGS_PARSER_H
