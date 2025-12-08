# Audigest - AI 视频/音频摘要工具

自动提取并总结视频/音频内容，支持多平台。

## 📋 功能特性

- 🎥 多平台支持：YouTube、Bilibili、小宇宙、X (Twitter)、通用播客
- 🎙️ 自动转录：使用 WhisperX 进行高质量语音识别
- 🤖 AI 总结：支持 DeepSeek、OpenAI、Ollama、PPIO 等多个 LLM 提供商
- ⚡ GPU 加速：支持 CUDA 加速转录过程
- 📊 结构化输出：生成摘要、金句、思维导图等

## 🚀 快速开始

### 前置要求

- Python 3.10 或 3.11
- [uv](https://github.com/astral-sh/uv) 包管理器
- NVIDIA GPU（可选，用于 CUDA 加速）

### 安装步骤

#### Windows

```powershell
# 1. 克隆项目
git clone https://github.com/xfrrn/Audigest.git
cd Audigest

# 2. 运行自动安装脚本
.\install.ps1
```

#### Linux/macOS

```bash
# 1. 克隆项目
git clone https://github.com/xfrrn/Audigest.git
cd Audigest

# 2. 添加执行权限并运行安装脚本
chmod +x install.sh
./install.sh
```

#### 手动安装

```bash
# 1. 安装主要依赖（包括 CUDA 版本的 PyTorch）
uv sync

# 2. 安装 WhisperX（不带依赖，避免覆盖 PyTorch）
uv pip install --python .venv/Scripts/python.exe --no-deps git+https://github.com/m-bain/whisperX.git

# 3. 验证安装
uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置 LLM API 密钥：

```env
# LLM 配置
DEFAULT_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
PPIO_API_KEY=your_api_key_here

# 代理配置（可选）
PROXY_URL=http://127.0.0.1:7890
```

## 💻 使用方法

### 运行项目

```bash
# 使用 uv run
uv run python your_script.py

# 或直接使用虚拟环境
.\.venv\Scripts\python.exe your_script.py  # Windows
./.venv/bin/python your_script.py          # Linux/macOS
```

### 测试 LLM

```bash
uv run python backend/services/test_llm.py
```

## 📚 支持的平台

## 📚 支持的平台

- **YouTube**：视频和 Shorts
- **Bilibili**：视频分享链接
- **小宇宙**：播客节目
- **X (Twitter)**：视频推文
- **通用播客**：RSS 订阅

### 示例链接

**Bilibili：**

- `https://www.bilibili.com/video/BV1mTSYBhEsR/`
- `BV1mTSYBhEsR`

**YouTube：**

- `https://www.youtube.com/watch?v=sja3KbtdJ_o`
- `https://youtu.be/sja3KbtdJ_o`
- `https://youtube.com/shorts/AC7wKqzrqAk`

**X (Twitter)：**

- `https://x.com/aramco/status/1994798865288237408`

**小宇宙：**

- `https://www.xiaoyuzhoufm.com/episode/692ec0773fec3166cfddd320`

## 🏗️ 技术栈

- **后端框架**：FastAPI + SQLModel
- **任务队列**：ARQ (Redis)
- **转录引擎**：WhisperX + FunASR
- **LLM 集成**：OpenAI SDK (支持多提供商)
- **包管理**：uv
- **GPU 加速**：PyTorch CUDA 11.8

## ⚙️ 重要说明

### PyTorch CUDA 配置

本项目使用 CUDA 11.8 版本的 PyTorch 以支持 GPU 加速。如果您的 GPU 不支持 CUDA 或只想使用 CPU：

1. 修改 `pyproject.toml` 中的 PyTorch 源
2. 或直接使用 CPU 版本：
   ```bash
   uv pip install torch torchvision torchaudio
   ```

### WhisperX 安装

WhisperX 必须使用 `--no-deps` 安装，以避免覆盖 CUDA 版本的 PyTorch。安装脚本已自动处理。

## 📖 参考项目

- **BiliGPT**：字幕预处理思路
- **Fabric**：Prompt Engineering
- **Podwise**：思维导图和金句提取
- **full-stack-fastapi-template**：项目架构参考

## 📝 开发

```bash
# 安装开发依赖
uv sync --group dev

# 运行测试
uv run pytest

# 代码格式化
uv run ruff format .
```

## 📄 许可证

MIT License

---

参考思路：

- BiliGPT:字幕预处理
- Fabric: Prompt Engineer
- Podwise: 思维导图，金句提取
- full-stack-fastapi-template: 学习如何组织 Celery/Redis 数据库
