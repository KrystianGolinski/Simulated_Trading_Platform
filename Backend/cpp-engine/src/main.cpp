#include "command_dispatcher.h"

int main(int argc, char* argv[]) {
    CommandDispatcher dispatcher;
    return dispatcher.execute(argc, argv);
}