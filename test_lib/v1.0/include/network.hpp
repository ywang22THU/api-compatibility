#ifndef LIBRARY_NETWORK_H
#define LIBRARY_NETWORK_H

#include "core.hpp"

class NetworkHandler {
public:
    NetworkHandler();
    virtual ~NetworkHandler();
    
    virtual Status connect(const char* address);
    virtual void disconnect();
    
    void send(const char* data) noexcept;
    
protected:
    void log(const char* message);
    
private:
    void* connection_;
};

#endif