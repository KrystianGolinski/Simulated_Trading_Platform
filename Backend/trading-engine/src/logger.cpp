#include "logger.h"

// Initialize static members
LogLevel Logger::current_level_ = LogLevel::INFO;  // Default to INFO level (no debug spam)
bool Logger::enabled_ = true;