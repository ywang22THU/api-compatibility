#ifndef LIBRARY_UTILS_H
#define LIBRARY_UTILS_H

#include "core.h"

int calculate(int a, int b);
double calculate(double a, double b);
float calculate(float a, float b);

template <typename T>
class Container {
public:
    Container(int size);
    ~Container();
    
    void add(const T& item);
    T get(int index) const;
    
    bool contains(const T& item) const;
    
private:
    T* data_;
    int size_;
    int count_;
};

constexpr int DEFAULT_SIZE = 512;

consteval int getMinSize() { return 16; }

#endif // LIBRARY_UTILS_H