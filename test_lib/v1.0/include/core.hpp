#ifndef LIBRARY_CORE_H
#define LIBRARY_CORE_H

#define API_VERSION 1
#define MAX_SIZE 1024

enum Status {
    OK = 0,
    ERROR = 1,
    TIMEOUT = 2
};

class BaseProcessor {
public:
    BaseProcessor(int id);
    virtual ~BaseProcessor();
    
    virtual void process();
    
    virtual void analyze() = 0;
    
    static constexpr int getMaxValue() { return 100; }
    
protected:
    int id_;
};

class DataProcessor : public BaseProcessor {
public:
    DataProcessor(int id, int bufferSize);
    ~DataProcessor() override;
    
    void process() override;
    void analyze() override;
    
    virtual void finalize() final;
    
    int transform(int input, double factor = 1.0);
    
private:
    int bufferSize_;
    char* buffer_;
};

#endif // LIBRARY_CORE_H