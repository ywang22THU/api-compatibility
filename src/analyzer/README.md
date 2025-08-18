# Analyzer 模块结构

这个目录包含了重构后的 API 兼容性分析器，采用了更加模块化和可维护的设计。

## 目录结构

```
analyzer/
├── __init__.py                 # 包初始化，导出主要接口
├── core/                       # 核心功能
│   ├── __init__.py
│   └── compatibility_checker.py # 主兼容性检查器，协调各个专门检查器
├── checkers/                   # 专门的兼容性检查器
│   ├── __init__.py
│   ├── base_checker.py        # 检查器基类
│   ├── class_checker.py       # 类兼容性检查器（包含函数兼容性检查）
│   ├── enum_checker.py        # 枚举兼容性检查器
│   └── macro_checker.py       # 宏兼容性检查器
├── models/                     # 数据模型
│   ├── __init__.py
│   └── compatibility_models.py # 兼容性相关的数据结构
└── utils/                      # 工具函数
    ├── __init__.py
    ├── loader.py              # API 数据加载器
    └── report_generator.py    # 报告生成器
```

## 主要组件

### 1. 核心模块 (core/)
- `CompatibilityChecker`: 主要的兼容性检查器，协调所有专门的检查器

### 2. 检查器模块 (checkers/)
- `BaseChecker`: 所有检查器的基类
- `ClassChecker`: 检查类的兼容性
- `FunctionChecker`: 检查全局函数的兼容性
- `EnumChecker`: 检查枚举的兼容性
- `MacroChecker`: 检查宏定义的兼容性

### 3. 模型模块 (models/)
- `CompatibilityLevel`: 兼容性级别枚举 (ERROR, CRITICAL, WARNING, INFO)
- `ChangeType`: 变更类型枚举
- `CompatibilityIssue`: 兼容性问题数据结构
- `IncompatibilityScore`: 不兼容性评分数据结构

### 4. 工具模块 (utils/)
- `load_api_from_json`: 从 JSON 文件加载 API 定义
- `ReportGenerator`: 生成各种格式的兼容性报告

## 使用方式

### 作为模块使用
```python
from analyzer import CompatibilityChecker, load_api_from_json, ReportGenerator

# 加载 API 数据
old_api = load_api_from_json('api_v1.json')
new_api = load_api_from_json('api_v2.json')

# 执行兼容性检查
checker = CompatibilityChecker()
issues = checker.check_compatibility(old_api, new_api)
summary = checker.generate_summary()
score = checker.calculate_incompatibility_score()

# 生成报告
report = ReportGenerator.generate_text_report(issues, summary, score)
print(report)
```

### 命令行使用
```bash
python api_compatibility_analyzer.py api_v1.json api_v2.json --format text -o report.txt
```

## 设计优势

1. **模块化**: 每个功能模块都有明确的职责
2. **可扩展**: 新的检查器可以轻松添加到 checkers/ 目录
3. **可维护**: 代码结构清晰，易于理解和修改
4. **可重用**: 各个组件可以独立使用
5. **类型安全**: 使用了明确的数据模型和类型提示

## 扩展指南

### 添加新的检查器
1. 在 `checkers/` 目录创建新的检查器文件
2. 继承 `BaseChecker` 类
3. 实现 `check()` 方法
4. 在 `checkers/__init__.py` 中导出新检查器
5. 在 `core/compatibility_checker.py` 中集成新检查器

### 添加新的报告格式
1. 在 `utils/report_generator.py` 中添加新的生成方法
2. 在主程序中添加新的格式选项

