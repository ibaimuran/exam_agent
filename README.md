# 试卷分析 Agent

基于 DeepSeek API 的智能试卷分析 Agent，支持试卷逐题知识点分析、学生错题归档与诊断、专属错题练习卷生成。

## 功能

| 模块 | 输入 | 输出 |
| --- | --- | --- |
| 试卷分析 | 上传 PDF/Word 试卷 | 逐题知识点分析 + Word 下载 |
| 错题归档 | 学生姓名 + 错题号 | 错题归档 + 学生诊断报告 + Word 下载 |
| 练习卷生成 | 学生姓名 | 专属错题练习卷 + Word 下载 |

## 技术栈

- 后端：Flask
- AI：DeepSeek API（兼容 OpenAI SDK）
- PDF 提取：pdfplumber / PyPDF2 / PyMuPDF
- OCR：CnOCR / EasyOCR / Tesseract（按优先级自动选择）
- Word 处理：python-docx
- 架构：Agent 模式（BaseAgent + Orchestrator + 子 Agent）

## 环境要求

- Python 3.10+

### OCR 系统依赖（可选）

扫描型 PDF（图片转文字）需要 OCR 支持，至少准备以下一种：

| OCR 引擎 | 安装方式 |
| --- | --- |
| CnOCR | `pip install cnocr`（纯 Python，中文优化，推荐） |
| EasyOCR | `pip install easyocr`（纯 Python，首次运行自动下载模型） |
| Tesseract | 系统安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) + `pip install pytesseract` |

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd exam_agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env          # 编辑 .env，填入 DeepSeek API Key
# 或直接创建 .env 文件：
# echo DEEPSEEK_API_KEY=sk-your-key > .env

# 4. 启动服务
python app.py local

# 5. 浏览器打开
# http://127.0.0.1:5000
```

## 项目结构

```
exam_agent/
├── app.py                       ← Flask API 层（3 个 API + 3 个下载端点）
├── config.py                    ← 排版/页面/试卷结构常量
├── agent/
│   ├── __init__.py
│   ├── base.py                  ← BaseAgent：DeepSeek API 封装
│   ├── orchestrator.py          ← ExamOrchestrator：协调 3 个子 Agent
│   ├── paper_agent.py           ← PaperAgent：PDF/Word 提取 + AI 分析 + Word 生成
│   ├── student_agent.py         ← StudentAgent：错题归档 + AI 诊断
│   └── exam_generator.py        ← ExamGeneratorAgent：AI 出题 + Word 排版
├── utils/
│   ├── __init__.py
│   ├── file_utils.py            ← PDF/Word 文字提取（含 OCR 回退链）
│   └── docx_utils.py            ← Word 文档生成共享函数
├── prompts/
│   ├── loader.py                ← Prompt 模板加载
│   ├── format_rules.txt         ← 化学式/离子符号格式规范
│   ├── paper_prompts.txt        ← 试卷分析 prompt
│   ├── student_prompts.txt      ← 学生诊断 prompt
│   └── exam_prompts.txt         ← 练习卷生成 prompt
├── templates/
│   └── index.html               ← 单页前端
├── students/                    ← 学生错题归档（JSON）
├── outputs/                     ← 生成的 Word 文件
├── .env                         ← DeepSeek API Key（已 gitignore）
└── requirements.txt
```

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/paper/upload` | 上传试卷文件（multipart/form-data） |
| GET | `/api/paper/download-docx` | 下载试卷分析 Word |
| POST | `/api/wrong/submit` | 提交错题归档（JSON） |
| GET | `/api/wrong/download-docx/<name>` | 下载学生诊断 Word |
| POST | `/api/wrong/generate-paper` | 生成错题练习卷 |
| GET | `/api/wrong/download-paper-docx/<name>` | 下载练习卷 Word |

## Agent 工作流

```
用户上传 PDF/Word
       ↓
PaperAgent：提取文字 → DeepSeek 逐题分析 → 生成 Word
       ↓
用户提交错题号
       ↓
StudentAgent：匹配错题 → AI 生成诊断报告 → 归档 JSON → 生成 Word
       ↓
用户请求错题卷
       ↓
ExamGeneratorAgent：读取错题记录 → AI 生成练习卷 → 生成 Word
```

## PDF 文字提取策略

系统按以下优先级依次尝试：

1. **pdfplumber** — 对表格和结构化文字效果好
2. **PyMuPDF (fitz)** — 对 CJK 字符和特殊编码支持好
3. **PyPDF2** — 通用 PDF 读取
4. **Tesseract OCR** — 需系统安装 Tesseract 引擎
5. **CnOCR** — 纯 Python 中文 OCR
6. **EasyOCR** — 纯 Python 多语言 OCR

## License

MIT