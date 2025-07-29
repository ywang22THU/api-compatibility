#ifndef LIBRARY_NEW_FEATURE_H
#define LIBRARY_NEW_FEATURE_H

#include "core.hpp"

class AdvancedProcessor : public BaseProcessor {
public:
    AdvancedProcessor(int id, int bufferSize);
    ~AdvancedProcessor() override;
    
    void analyze() override;
    void validate() const override;
    
    // 新方法
    void optimize();
    
private:
    int advancedFlag_;
};

#endif