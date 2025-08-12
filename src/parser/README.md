# Parser 模块

这是 API 兼容性分析工具的 C++ 头文件解析器模块，使用正则表达式解析 C++ 代码并提取 API 信息。

## 模块结构

```
parser/
├── __init__.py                 # 模块初始化文件
├── README.md                   # 本文档
├── core/                       # 核心解析器
│   ├── __init__.py
│   ├── base_parser.py          # 基础解析器抽象类
│   ├── cpp_parser.py           # C++ 主解析器
│   ├── class_parser.py         # 类解析器
│   ├── function_parser.py      # 函数解析器
│   ├── enum_parser.py          # 枚举解析器
│   └── macro_parser.py         # 宏解析器
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── api_definition.py       # API 定义根模型
│   ├── class_models.py         # 类相关模型
│   ├── function.py             # 函数模型
│   ├── enum_models.py          # 枚举模型
│   ├── macro.py                # 宏模型
│   ├── member.py               # 成员模型
│   └── parameter.py            # 参数模型
└── utils/                      # 工具函数
    ├── __init__.py
    ├── serializer.py           # 序列化工具
    └── text_processor.py       # 文本处理工具
```

## 核心组件

### 核心解析器 (`core/`)

#### BaseParser
- 文件: `base_parser.py`
- 功能: 提供所有解析器的基础抽象类
- 主要方法:
  - `preprocess_text()`: 预处理文本，移除注释和预编译指令
  - `parse()`: 抽象解析方法

#### CppParser
- 文件: `cpp_parser.py`
- 功能: C++ 头文件的主解析器，协调各个子解析器
- 主要功能:
  - 解析整个 C++ 头文件
  - 提取类、函数、枚举、宏定义
  - 生成完整的 API 定义

#### 专属解析器
- ClassParser (`class_parser.py`): 解析 C++ 类定义
- FunctionParser (`function_parser.py`): 解析全局函数
- EnumParser (`enum_parser.py`): 解析枚举类型
- MacroParser (`macro_parser.py`): 解析宏定义

### 数据模型 (`models/`)

#### APIDefinition
- 文件: `api_definition.py`
- 功能: 根数据模型，包含所有解析的 API 信息
- 包含:
  - 文件列表
  - 类定义列表
  - 函数定义列表
  - 枚举定义列表
  - 宏定义列表

#### 数据模型类
- `ClassModel`: 类定义模型
- `Function`: 函数定义模型
- `EnumModel`: 枚举定义模型
- `Macro`: 宏定义模型
- `Member`: 类成员变量模型
- `Parameter`: 函数参数模型

### 工具函数 (`utils/`)

#### TextProcessor
- 文件: `text_processor.py`
- 功能: 文本预处理工具
- 主要方法:
  - `remove_comments()`: 移除 C++ 注释（单行和多行）
  - `remove_preprocessor_directives()`: 移除预编译指令
  - `preprocess_code()`: 完整的代码预处理

#### Serializer
- 文件: `serializer.py`
- 功能: 序列化和反序列化工具
- 支持格式: JSON

## 使用示例

### 基本解析

```python
from parser.core.cpp_parser import CppParser

# 创建解析器
parser = CppParser()

# 解析单个文件
with open('example.h', 'r', encoding='utf-8') as f:
    content = f.read()

api_def = parser.parse_file(content, 'example.h')

# 解析多个文件
file_paths = ['header1.h', 'header2.h']
api_def = parser.parse_files(file_paths)
```

### 序列化到 JSON

```python
from parser.utils.serializer import Serializer

# 保存解析结果
serializer = Serializer()
serializer.save_to_json(api_def, 'api_data.json')

# 加载解析结果
loaded_api_def = serializer.load_from_json('api_data.json')
```

### 文本预处理

```python
from parser.utils.text_processor import TextProcessor

processor = TextProcessor()

# 移除注释
clean_code = processor.remove_comments(cpp_code)

# 移除预编译指令
clean_code = processor.remove_preprocessor_directives(cpp_code)

# 完整预处理
clean_code = processor.preprocess_code(cpp_code)
```

## 解析特性

### 支持的 C++ 特性

1. 类定义
   - 类声明和定义
   - 继承关系
   - 成员变量（包括访问权限）
   - 成员函数（包括虚函数、纯虚函数）
   - 构造函数和析构函数

2. 函数定义
   - 全局函数
   - 函数重载
   - 函数参数（包括默认参数）
   - 返回类型
   - 异常规范

3. 枚举类型
   - 传统枚举
   - 强类型枚举（enum class）
   - 枚举值

4. 宏定义
   - 简单宏定义
   - 带参数的宏
   - 头文件保护宏
   - 条件编译宏

### 预处理功能

1. 注释移除
   - 单行注释 (`//`)
   - 多行注释 (`/* */`)
   - 嵌套注释处理

2. 预编译指令处理
   - 忽略 `#include` 指令
   - 忽略 `#pragma` 指令
   - 特殊处理条件编译指令（`#ifndef`, `#endif` 等）
   - 保留 `#define` 宏定义

3. 文本清理
   - 移除多余空白
   - 标准化换行符

## 扩展开发

### 添加新的解析器

1. 继承 `BaseParser` 类
2. 实现 `parse()` 方法
3. 在 `CppParser` 中集成新解析器

### 添加新的数据模型

1. 定义新的数据类
2. 在 `APIDefinition` 中添加相应字段
3. 更新序列化逻辑

### 自定义文本处理

1. 扩展 `TextProcessor` 类
2. 添加新的预处理方法
3. 在解析流程中集成

