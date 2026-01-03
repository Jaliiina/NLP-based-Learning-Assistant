# 📚 基于 NLP 的讲义助学工具

> Lecture Assistant · NLP-powered Study Helper

一个面向课程讲义、教材、课件文本的智能助学系统，以 NLP 技术为核心，构建从「文本理解」到「学习辅助生成」的完整助学流程。

## ✨ 功能特性

### 📘 主线功能 | 讲义理解
- **数据加载与预处理**：支持 TXT/DOCX/PDF/CSV 多格式文件，自动清洗、分词、去停用词
- **智能词云生成**：基于 TF-IDF / TextRank 算法，按章节或全局生成关键词词云
- **摘要与核心知识点**：自动提取讲义摘要，识别核心知识点，生成学习建议

### 🧰 工具模块 | 进阶分析
- **段落关键词分析**：TF-IDF 段落级关键词提取，定位高信息密度段落
- **多类型习题生成**：基于 DeepSeek 大模型，自动生成概念题/理解题/简答题
- **语义理解与概念关联**：Word2Vec 词向量训练与可视化，探索术语语义关系
- **标题生成与主题提炼**：Seq2Seq + Attention 模型生成学术标题，LDA 提取关键词
- **视觉摘要生成器**：CLIP 引导图像优化，将摘要转化为视觉内容
- **梯度下降可视化**：交互式算法演示，支持自定义函数与参数调节

## 📁 项目结构

```
aid_integrated/
├── app.py                 # 主应用入口
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
│
├── auth/                  # 用户认证模块
│   ├── db.py             # 数据库操作
│   ├── service.py        # 认证服务
│   └── ui.py             # 登录/注册界面
│
├── campus/                # 讲义处理模块
│   ├── file_utils.py     # 文件加载
│   ├── text_cleaner.py   # 文本清洗
│   ├── wordcloud_utils.py # 词云生成
│   ├── summary_utils.py  # 摘要提取
│   ├── llm_helpers.py    # LLM 辅助
│   ├── question.py       # 习题生成
│   └── stopwords.txt     # 停用词表
│
├── nlp/                   # NLP 实验模块
│   ├── app.py            # TF-IDF & Word2Vec
│   └── stopwords.txt     # 停用词表
│
├── c1218/                 # 内容生成模块
│   ├── titlegen_app.py   # 标题生成
│   ├── tti_app.py        # 视觉摘要
│   └── resources/        # 模型文件
│
├── gradient_descent/      # 算法可视化模块
│   └── gra_app.py        # 梯度下降演示
│
├── pages/                 # 页面路由
│   ├── index.py          # 系统介绍
│   ├── campus_*.py       # 讲义处理页面
│   ├── nlp_*.py          # NLP 实验页面
│   ├── c1218_*.py        # 内容生成页面
│   └── admin_users.py    # 用户管理
│
├── data/                  # 数据目录
│   └── app.db            # SQLite 数据库
│
└── .streamlit/
    └── secrets.toml      # API 密钥配置
```

### 🔐 系统功能
- 用户认证（注册/登录）
- 角色权限管理（普通用户/管理员）
- 全局对话助手（基于 DeepSeek）

## 🛠️ 环境要求

- Python 3.10+
- Windows / macOS / Linux

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd aid_integrated
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用 conda
conda create -n nlp_aid python=3.11
conda activate nlp_aid

# 或使用 venv
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装中文字体（词云功能需要）

确保系统中存在中文字体文件，默认使用 `C:/Windows/Fonts/simhei.ttf`（黑体）。

macOS/Linux 用户需修改 `campus/wordcloud_utils.py` 中的字体路径。

### 5. 配置 API 密钥

在项目目录下创建 `.streamlit/secrets.toml` 文件：

```toml
# DeepSeek API（对话助手、摘要优化、习题生成）
DEEPSEEK_API_KEY = "your-deepseek-api-key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"  # 可选
DEEPSEEK_MODEL = "deepseek-chat"  # 可选

# Zhipu API（视觉摘要对比功能，可选）
ZHIPU_API_KEY = "your-zhipu-api-key"

# MiniMax API（TTS 朗读功能，可选）
MINIMAX_GROUP_ID = "your-group-id"
MINIMAX_API_KEY = "your-minimax-api-key"
```

> 💡 不配置 API 密钥也可使用大部分功能，仅对话助手、摘要优化、习题生成等功能不可用。

## 🚀 启动应用

```bash
streamlit run app.py
```

启动后浏览器会自动打开 `http://localhost:8501`

## 📖 使用指南

### 首次使用

1. **注册账号**：在登录页面点击「注册」，填写用户名、邮箱、密码
2. **登录系统**：使用注册的账号登录

### 推荐使用流程

```
📚 数据加载与预处理
        ↓
   上传讲义文件（支持多文件）
        ↓
   执行文本清洗
        ↓
☁️ 智能词云生成 ←→ 📋 摘要与核心知识点
        ↓
📈 段落关键词分析 / 📘 多类型习题生成
        ↓
🧠 语义理解与概念关联（可选）
```

### 各模块使用说明

#### 📚 数据加载与预处理
1. 上传讲义文件（支持批量上传，每个文件对应一个章节）
2. 配置预处理参数（转小写、移除公式、数字处理、去停用词）
3. 点击「执行文本清洗」
4. 预览清洗结果

#### ☁️ 智能词云生成
1. 选择生成模式（按章节 / 全局）
2. 选择权重模型（TF-IDF / TextRank）
3. 调整词云参数（背景色、最大词数）
4. 点击「生成智能词云」

#### 📋 摘要与核心知识点
1. 选择生成模式（按章节 / 全局）
2. 选择摘要长度（50/100/150 字符）
3. 可选：启用 DeepSeek 优化
4. 点击「生成摘要与核心知识点」

#### 📈 段落关键词分析
1. 在文本框中粘贴或编辑讲义内容（用空行分段）
2. 调整参数（n-gram 长度、特征数量、是否使用 jieba 分词）
3. 选择段落查看关键词
4. 查看重点段落排行

#### 📘 多类型习题生成
1. 确保已在「摘要与核心知识点」页面生成核心内容
2. 选择出题范围（全局 / 按章节）
3. 选择题型（概念解释题、关键句理解题、简答题）
4. 可选：填写出题要求
5. 点击「生成复习题」

#### 🧠 语义理解与概念关联
1. 选择模型来源（预训练模型 / 自训练）
2. 如自训练：粘贴语料，调整参数，点击「开始训练模型」
3. 输入术语查询相似词
4. 选择降维方法（PCA / t-SNE），点击「开始可视化」

#### 🧩 标题生成与主题提炼
1. 粘贴摘要内容
2. 可选：调整生成参数
3. 点击「生成标题与关键词」

#### 🧬 视觉摘要生成器
1. 输入摘要内容
2. 选择 Prompt 风格
3. 点击「根据摘要生成 Prompt」
4. 调整生成参数
5. 点击「生成图像」

#### 📉 梯度下降可视化
1. 选择功能模式（经典函数案例 / 自定义函数）
2. 调整参数（学习率、迭代次数、初始点）
3. 点击「开始梯度下降」
4. 拖动滑块查看迭代过程

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| 前端框架 | Streamlit |
| 中文分词 | jieba |
| 特征提取 | scikit-learn (TF-IDF, LDA, PCA) |
| 词向量 | gensim (Word2Vec) |
| 深度学习 | PyTorch (Seq2Seq, CLIP) |
| 数据可视化 | Matplotlib, WordCloud |
| 数据库 | SQLite |
| 密码加密 | bcrypt |
| 大语言模型 | DeepSeek API |

## ❓ 常见问题

### Q: 词云显示乱码？
A: 检查中文字体路径是否正确，Windows 默认使用 `C:/Windows/Fonts/simhei.ttf`

### Q: DeepSeek 功能不可用？
A: 请在 `.streamlit/secrets.toml` 中配置 `DEEPSEEK_API_KEY`

### Q: 标题生成报错找不到模型？
A: 确保 `c1218/resources/attn_lstm_titlegen.pt` 模型文件存在

### Q: 如何重置管理员密码？
A: 删除 `data/app.db` 文件后重新注册（会清空所有用户数据）

## 📄 许可证

本项目仅供学习交流使用。
