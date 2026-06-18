# Code Review Agent 🔍

基于 Claude + LangGraph + RAG 的智能多Agent代码审查系统

## 项目简介

本项目实现了一个自动化代码审查系统，通过多个AI Agent协同工作，对代码进行全面分析，输出包含Bug、安全漏洞、性能问题和风格建议的结构化审查报告，并自动生成修复代码和质量评分。

## 系统架构

    用户输入代码 / 上传文件
          ↓
    Supervisor Agent  →  检测编程语言，设置语言专项审查重点
          ↓
    Retriever Agent   →  从知识库检索相关上下文
          ↓
    Analyzer Agent    →  调用Claude分析Bug/安全/性能/风格
          ↓
    Fixer Agent       →  根据问题自动生成修复后的完整代码
          ↓
    Reviewer Agent    →  汇总结果，生成结构化报告
          ↓
    Evaluator Agent   →  LLM-as-Judge，对审查报告质量打分（0-100）
          ↓
    Streamlit 前端展示 / 历史记录回溯

## 技术栈

- **LangGraph** — Multi-Agent状态机调度
- **LangChain** — RAG检索链路
- **Claude API (claude-sonnet-4-6)** — 代码分析LLM后端
- **ChromaDB** — 本地向量数据库
- **HuggingFace Embeddings (all-MiniLM-L6-v2)** — 代码向量化
- **Streamlit** — 前端交互界面

## 主要功能

- 自动检测代码Bug和潜在错误
- 识别安全漏洞（硬编码密码、注入风险等）
- 分析性能瓶颈
- 检查代码风格规范（PEP8等）
- 输出0-100综合评分
- **自动语言检测**：Supervisor Agent识别Python/JavaScript/Java/TypeScript等语言，按语言特性调整审查重点
- **多语言支持**：支持上传 `.py` `.js` `.java` `.ts` 文件，自动读取内容填入代码框
- **文件上传**：拖拽或点击上传代码文件，免去手动粘贴
- **自动修复代码**：Fixer Agent针对所有发现问题生成修复后的完整代码
- **LLM-as-Judge 评估**：Evaluator Agent从问题描述具体性、修复可行性、误报率三个维度对审查报告打质量分
- **历史记录**：侧边栏展示所有历史审查，点击可通过 `graph.get_state` 恢复完整报告

## 快速开始

### 环境要求

- Python 3.11+
- Anthropic API Key

### 安装

```bash
git clone https://github.com/ytia0058/code-review-agent.git
cd code-review-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 配置

在项目根目录新建 `.env` 文件：

```
ANTHROPIC_API_KEY=你的key
```

### 运行

```bash
streamlit run app.py
```

访问 http://localhost:8501

## 项目结构

```
code-review-agent/
├── src/
│   ├── agents/
│   │   ├── analyzer.py   # 代码分析Agent
│   │   └── graph.py      # LangGraph多Agent调度
│   └── rag/
│       └── indexer.py    # RAG索引与检索
├── sample_code/          # 示例代码
├── app.py                # Streamlit前端
├── requirements.txt      # 依赖列表
└── README.md
```

## 架构决策

- **为什么选LangGraph而不是AutoGen**：LangGraph的StateGraph提供更细粒度的状态控制，适合需要明确数据流向的审查场景，Agent间状态传递更可控
- **为什么用本地Embedding而不是OpenAI**：使用HuggingFace的all-MiniLM-L6-v2，零成本、离线可用，对代码检索场景效果足够
- **为什么选ChromaDB**：本地部署无需服务器，开发阶段轻量易用，后期可无缝迁移到pgvector
- **为什么加Evaluator（LLM-as-Judge）**：人工审核每一份审查报告成本高且不可扩展；Evaluator用同一个Claude模型从三个维度对报告质量打分，输出可量化的 `quality_score`，替代人工抽检，同时为后续优化Analyzer prompt提供客观反馈信号

## License

MIT