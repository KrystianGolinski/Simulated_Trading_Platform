#pragma once

#include <iostream>
#include <string>
#include <sstream>

enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3
};

class Logger {
private:
    static LogLevel current_level_;
    static bool enabled_;

public:
    static void setLevel(LogLevel level) {
        current_level_ = level;
    }
    
    static void setEnabled(bool enabled) {
        enabled_ = enabled;
    }
    
    static bool isLevelEnabled(LogLevel level) {
        return enabled_ && level >= current_level_;
    }
    
    template<typename... Args>
    static void log(LogLevel level, Args&&... args) {
        if (!isLevelEnabled(level)) return;
        
        std::ostringstream oss;
        const char* level_str = getLevelString(level);
        oss << "[" << level_str << "] ";
        (oss << ... << args);
        std::cerr << oss.str() << std::endl;
    }
    
    template<typename... Args>
    static void debug(Args&&... args) {
        log(LogLevel::DEBUG, std::forward<Args>(args)...);
    }
    
    template<typename... Args>
    static void info(Args&&... args) {
        log(LogLevel::INFO, std::forward<Args>(args)...);
    }
    
    template<typename... Args>
    static void warning(Args&&... args) {
        log(LogLevel::WARNING, std::forward<Args>(args)...);
    }
    
    template<typename... Args>
    static void error(Args&&... args) {
        log(LogLevel::ERROR, std::forward<Args>(args)...);
    }

private:
    static const char* getLevelString(LogLevel level) {
        switch (level) {
            case LogLevel::DEBUG: return "DEBUG";
            case LogLevel::INFO: return "INFO";
            case LogLevel::WARNING: return "WARNING";
            case LogLevel::ERROR: return "ERROR";
            default: return "UNKNOWN";
        }
    }
};