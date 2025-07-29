#ifndef LIBRARY_NETWORK_H
#define LIBRARY_NETWORK_H

#include "core.hpp"

class SecureNetworkHandler : public NetworkHandler {
public:
    SecureNetworkHandler();
    ~SecureNetworkHandler() override;
    Status connect(const char* address) override;
    
    void encrypt(bool enable);
};

class NetworkHandler {
public:
    NetworkHandler();
    virtual ~NetworkHandler();
    
    virtual Status connect(const char* address) noexcept;
    
    virtual void disconnect();
    
    void send(const char* data, int length);
    
protected:
    void log(const char* message);
    
private:
    void* connection_;
};

#endif // LIBRARY_NETWORK_H