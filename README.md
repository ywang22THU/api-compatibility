# API兼容性分析工具

这是一个用于分析C++ API版本间兼容性的工具集，可以解析C++头文件并生成详细的兼容性分析报告。

## 项目简介

该项目提供了两个主要工具：

1. lib_parse.py - C++头文件解析器，使用libclang解析C++代码并提取API信息
2. api_compatibility_analyzer.py - API兼容性分析器，比较两个版本的API并生成兼容性报告

## 功能特性

### C++头文件解析器 
- 解析C++头文件中的类、函数、枚举、宏定义
- 提取详细的API信息，包括：
  - 函数签名、返回类型、参数列表
  - 类的继承关系、成员变量、成员函数
  - 枚举类型和枚举值
  - 访问权限、虚函数属性等
- 输出结构化的JSON格式API数据

### API兼容性分析器 
- 比较两个版本的API JSON文件
- 检测各种类型的兼容性问题：
  - ERROR级别：破坏性变更，会导致编译失败
  - CRITICAL级别：严重的行为变更，可能导致运行时错误
  - WARNING级别：可能影响功能的变更
  - INFO级别：信息性变更，通常是新增功能
- 生成详细的兼容性分析报告
- 
## 使用方法

### 解析C++头文件

#### 基本用法

```bash
python src/lib_parse.py --root_path /path/to/cpp/library --output_path api_v1.json
```

#### 排除特定目录
```bash
# 使用默认排除目录（3rdparty, tests, icons等）
python src/lib_parse.py --root_path /path/to/cpp/library --output_path api_v1.json

# 自定义排除目录
python src/lib_parse.py --root_path /path/to/cpp/library --exclude_dirs 3rdparty tests build --output_path api_v1.json

# 不排除任何目录
python src/lib_parse.py --root_path /path/to/cpp/library --exclude_dirs --output_path api_v1.json
```

参数说明：
- `--root_path`: C++库的根目录路径，包含头文件（必需）
- `--output_path`: 输出的JSON文件路径（默认：api_data.json）
- `--exclude_dirs`: 要排除的目录名称列表（默认：['3rdparty', 'third_party', 'thirdparty', 'icons', 'tests', 'test', 'examples', 'example', 'docs', 'doc', 'build', 'cmake-build-debug', 'cmake-build-release', '.git', '.vscode', '__pycache__']）
- `-vvv, --verbose`: 启用详细输出

#### 支持的构建系统

1. CMake项目
   - 自动运行 `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`
   - 从 `compile_commands.json` 提取编译参数
   - 支持指定构建目录和CMake参数

2. Makefile项目  
   - 运行 `make -n` 获取编译命令
   - 解析Makefile中的CXXFLAGS、INCLUDES等变量
   - 支持指定特定目标

3. 自动检测
   - 检查项目根目录中的 CMakeLists.txt 或 Makefile
   - 自动选择合适的构建系统
   - 支持多种构建系统（Gradle、Meson、Autotools等）

### 分析API兼容性

```bash
python src/api_compatibility_analyzer.py api_v1.json api_v2.json -o compatibility_report.json
```

参数说明：
- `api_v1.json`: 第一个版本的API JSON文件
- `api_v2.json`: 第二个版本的API JSON文件
- `-o, --output`: 输出报告文件路径（可选，默认 `stdout`）
- `--format`: 输出格式，支持 `text` 或 `json`（默认）

## 支持的兼容性检查

### 文件级别
- 头文件删除
- 头文件新增

### 枚举类型
- 枚举删除
- 枚举新增
- 枚举值删除
- 枚举值变更
- 枚举值新增

### 类
- 类删除
- 类新增
- 基类删除/新增
- 成员变量删除/新增/类型变更
- 成员变量访问权限变更
- 成员函数删除/新增
- 成员函数返回类型变更
- 成员函数异常规范变更
- 成员函数虚函数属性变更
- 成员函数访问权限变更

### 全局函数
- 函数删除
- 函数新增
- 函数返回类型变更

## 兼容性等级说明

| 等级 | 描述 | 影响 |
|------|------|------|
| ERROR | 破坏性变更 | 会导致编译失败 |
| CRITICAL | 严重的行为变更 | 可能导致运行时错误 |
| WARNING | 可能影响功能的变更 | 需要注意但不会立即失败 |
| INFO | 信息性变更 | 通常是新增功能，向后兼容 |

## 限制和注意事项

1. 依赖libclang - 需要正确配置libclang环境
2. 编译标志 - 可能需要根据项目调整编译标志
3. 模板支持 - 对复杂模板的支持可能有限
4. 宏展开 - 不会展开宏定义，可能影响解析结果
