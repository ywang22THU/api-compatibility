# Makefile for test_lib v1.0
# Simple C++ library build system

# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++14 -Wall -Wextra -O2 -fPIC
CPPFLAGS = -Iinclude
LDFLAGS = -shared

# Directories
SRCDIR = src
INCDIR = include
OBJDIR = obj
LIBDIR = lib

# Source files
SOURCES = $(wildcard $(SRCDIR)/*.cpp)
OBJECTS = $(SOURCES:$(SRCDIR)/%.cpp=$(OBJDIR)/%.o)
HEADERS = $(wildcard $(INCDIR)/*.hpp)

# Library target
LIBRARY = $(LIBDIR)/libtest_v1.so
STATIC_LIB = $(LIBDIR)/libtest_v1.a

# Default target
.PHONY: all clean shared static install

all: shared static

shared: $(LIBRARY)

static: $(STATIC_LIB)

# Create shared library
$(LIBRARY): $(OBJECTS) | $(LIBDIR)
	$(CXX) $(LDFLAGS) -o $@ $^

# Create static library
$(STATIC_LIB): $(OBJECTS) | $(LIBDIR)
	ar rcs $@ $^

# Compile source files
$(OBJDIR)/%.o: $(SRCDIR)/%.cpp $(HEADERS) | $(OBJDIR)
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -c $< -o $@

# Create directories
$(OBJDIR):
	mkdir -p $(OBJDIR)

$(LIBDIR):
	mkdir -p $(LIBDIR)

# Clean build artifacts
clean:
	rm -rf $(OBJDIR) $(LIBDIR)

# Install library (optional)
install: $(LIBRARY) $(STATIC_LIB)
	cp $(LIBRARY) /usr/local/lib/
	cp $(STATIC_LIB) /usr/local/lib/
	cp -r $(INCDIR)/* /usr/local/include/

# Debug: show variables
debug:
	@echo "CXX: $(CXX)"
	@echo "CXXFLAGS: $(CXXFLAGS)"
	@echo "CPPFLAGS: $(CPPFLAGS)"
	@echo "SOURCES: $(SOURCES)"
	@echo "OBJECTS: $(OBJECTS)"
	@echo "HEADERS: $(HEADERS)"

# Help
help:
	@echo "Available targets:"
	@echo "  all     - Build both shared and static libraries (default)"
	@echo "  shared  - Build shared library (.so)"
	@echo "  static  - Build static library (.a)"
	@echo "  clean   - Remove build artifacts"
	@echo "  install - Install libraries to system"
	@echo "  debug   - Show build variables"
	@echo "  help    - Show this help message"
