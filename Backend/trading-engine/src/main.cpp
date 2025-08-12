#include "command_dispatcher.h"
#include "logger.h"

int main(int argc, char* argv[]) {
    // Logging Configuration:
    // - LogLevel::DEBUG: Shows everything (debug, info, warning, error) - use for debugging
    // - LogLevel::INFO: Shows info, warning, error (default) - production setting
    // - LogLevel::WARNING: Shows warning, error only - minimal output
    // - LogLevel::ERROR: Shows error only - critical issues only
    // - Logger::setEnabled(false): Completely disable all logging
    Logger::setLevel(LogLevel::INFO);
    
    CommandDispatcher dispatcher;
    return dispatcher.execute(argc, argv);
}