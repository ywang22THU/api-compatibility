#ifndef LIBRARY_CORE_H
#define LIBRARY_CORE_H

#define API_VERSION 2
#define MAX_SIZE 2048

enum Status {
    OK = 0,
    ERROR = 1,
    TIMEOUT = 2,
    RETRY = 3
};

class BaseProcessor {
public:
    BaseProcessor(int id);
    virtual ~BaseProcessor();
    
    virtual void process(int priority = 1);
    
    virtual void analyze() = 0;
    
    virtual void validate() const;
    
    static constexpr int getMaxValue() { return 200; }
    
protected:
    int id_;
};

class DataProcessor final : public BaseProcessor {
public:
    DataProcessor(int id, int bufferSize);
    ~DataProcessor() override;
    
    void process(int priority = 1) override;
    void analyze() override;

    virtual void finalize();

    double transform(double input, double factor = 1.0);
    
    void reset();
    
private:
    int bufferSize_;
    char* buffer_;
};

#endif // LIBRARY_CORE_H