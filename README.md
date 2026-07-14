# MathPad

手写数学公式识别工具 — 手写 → LaTeX → 一键复制

## 安装

```bash
# 1. 创建 Python 3.12 环境
conda create -n mathpad python=3.12 -y
conda activate mathpad

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载模型 (~410MB, 仅一次)
python download_model.py
```

## 运行

```bash
conda activate mathpad
python main.py
```

## 使用

1. 在画布上手写公式
2. 点击 **Recognize** — 首次需等待模型加载（后台加载，约 5-10s）
3. 左下角滑块切换显示模式：
   - **Text** — 可复制的 Unicode 数学符号（如 ∑ₓ²）
   - **LaTeX** — 原始 LaTeX 代码
4. 点击 **Clear** 清空画布
