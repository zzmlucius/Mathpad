i# MathPad 最小可用版本开发流程

## 目标

使用 **纯 Python** 实现一个最小版本：

* 打开一个窗口
* 鼠标/触摸板
* 转成图片
* 调用识别脚本
* 显示Latex/text结果

**只实现最基本功能，不做优化**

---

## 技术方案

* GUI：PyQt6（或 PySide6）
* 图像处理：Qt 内置（QPainter / QImage）
* 后端识别：Python 脚本
* 通信：直接函数调用 / subprocess

---

## 开发流程

---

## Step 1：创建窗口

### 目标

显示一个基础窗口。

---

### 要做的事

* 安装依赖：

```bash
pip install PyQt6
```

* 创建一个窗口类
* 设置固定大小（如 800×400）
* 有一部分书写位置，以及一行输出框（用于复制）

---

### 验收标准

* 能成功运行窗口

---

## Step 2：实现手写功能

### 目标

可以用鼠标在窗口上画线。

---

### 实现逻辑

#### 1. 数据结构

```python
strokes = []  # 所有笔画
current_stroke = []
```

---

#### 2. 鼠标事件

* `mousePressEvent`：开始新 stroke
* `mouseMoveEvent`：记录点
* `mouseReleaseEvent`：结束 stroke

---

#### 3. 绘制

在 `paintEvent` 中：

* 使用 `QPainter`
* 遍历所有 strokes
* 用 `drawLine` 连接点

---

### 验收标准

* 可以连续画线
* 多笔画正常显示

---

## Step 3：添加按钮

### 目标

点击按钮触发识别流程，以及点击按钮清空画布。

---

### 要做的事

* 添加两个按钮（clear 和 recognize）
* 绑定点击事件

---

## Step 4：笔迹转图片

### 目标

将 strokes 渲染为 PNG。

---

### 实现步骤

1. 创建 `QImage`
2. 使用 `QPainter` 重绘 strokes
3. 保存为 `temp.png`

---

### 验收标准

* 生成图片文件
* 内容与手写一致

---

## Step 5：调用识别脚本

### 目标

执行 Python 脚本并获取结果。
model : 

---

### 实现方式

使用 `subprocess`：

```python
import subprocess

result = subprocess.check_output(
    ["python", "recognize.py", "temp.png"]
)
```

---

### 输出约定

`recognize.py` 输出：

```text
x^2 + y^2
```

---

### 验收标准

* 能调用脚本
* 能获取返回结果

---

## Step 6：显示结果

### 目标

在界面上展示识别结果。

---

### 要做的事

* 添加 `QLabel` 或 `QTextEdit`
* 显示识别文本

---

## Step 7：复制到剪贴板

### 目标

让结果可以直接复制。

---

### 实现

```python
from PyQt6.QtGui import QGuiApplication

clipboard = QGuiApplication.clipboard()
clipboard.setText(result)
```

---

### 验收标准

* 能粘贴到其他应用

---

## Step 8：实现识别脚本

### 目标

写一个最简单可运行的识别程序。

---

### 后续替换

* Pix2Tex

---

## ✅ 最终流程

```text
启动程序
   ↓
鼠标手写
   ↓
点击“识别”
   ↓
生成 temp.png
   ↓
调用 recognize.py
   ↓
返回文本
   ↓
显示结果
   ↓
复制到剪贴板
```

---

## MVP 完成标准

满足以下即可：

* 能画
* 能生成图片
* 能调用识别
* 能显示结果
* 能复制

---

## 不包含内容

以下不在最小版本中：

* 快捷键唤出
* 实时识别
* 性能优化
* UI美化
* 模型优化
* 多行输入
* 撤销功能

---

## 总结

这个 Python 版本的核心是：

> 用最少代码打通完整链路：
> **手写 → 图片 → 识别 → 输出**

只要这条链路跑通，后续可以再逐步替换优化。

