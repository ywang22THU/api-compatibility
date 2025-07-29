#ifndef LIBRARY_UTILS_H
#define LIBRARY_UTILS_H

#include "core.hpp"

int calculate(int a, int b);
double calculate(double a, double b);

template <typename T>
class Container {
public:
    Container(int size);
    ~Container();
    
    void add(const T& item);
    T get(int index) const;
    
private:
    T* data_;
    int size_;
    int count_;
};

constexpr int DEFAULT_SIZE = 256;

#endif