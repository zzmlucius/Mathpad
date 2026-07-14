"""下载 UniMERNet 模型权重 (~410MB)，仅需运行一次"""
import os
import sys

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "unimernet_tiny")
CHECKPOINT = os.path.join(MODEL_DIR, "unimernet_tiny.pth")


def main():
    if os.path.exists(CHECKPOINT):
        print(f"模型已存在: {CHECKPOINT}")
        print(f"大小: {os.path.getsize(CHECKPOINT) / 1024**2:.0f} MB")
        return

    print("正在下载 UniMERNet tiny 模型 (~410MB)...")
    print("（如果网络慢，可手动从 HF 下载放入 models/unimernet_tiny/）")

    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            "wanderkid/unimernet_tiny",
            local_dir=MODEL_DIR,
        )
        print(f"完成！模型已保存到 {MODEL_DIR}")
    except Exception as e:
        print(f"下载失败: {e}")
        print(f"\n请手动下载 https://huggingface.co/wanderkid/unimernet_tiny")
        print(f"将所有文件放入 {os.path.abspath(MODEL_DIR)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
