"""UniMERNet 推理脚本 - 接收图片路径，输出 LaTeX
单次模式: python unimernet_infer.py <image.png>
服务模式: python unimernet_infer.py  (从stdin逐行读图片路径)
"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import torch
from PIL import Image
from omegaconf import OmegaConf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from unimernet.models.unimernet.unimernet import UniMERModel
from unimernet.processors import load_processor
import unimernet

PKG_DIR = os.path.dirname(unimernet.__file__)


class FormulaRecognizer:
    """数学公式识别器"""

    def __init__(self, model_dir: str, checkpoint: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model_cfg = OmegaConf.load(
            os.path.join(PKG_DIR, "configs", "models", "unimernet_base.yaml")
        )
        model_cfg = model_cfg.model
        model_cfg.tokenizer_config.path = model_dir
        model_cfg.pretrained = checkpoint
        model_cfg.model_name = model_dir
        model_cfg.model_config.model_name = model_dir

        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                self.model = UniMERModel.from_config(model_cfg).to(self.device)
                self.model.load_checkpoint(checkpoint)
            finally:
                sys.stdout = old_stdout
        self.model.eval()

        self.vis_processor = load_processor(
            "formula_image_eval",
            {"name": "formula_image_eval", "image_size": [192, 672]},
        )

    def predict(self, image_path: str) -> str:
        raw_image = Image.open(image_path).convert("RGB")
        image = self.vis_processor(raw_image).unsqueeze(0).to(self.device)
        output = self.model.generate({"image": image})
        return output["pred_str"][0]


def load_model():
    base_dir = os.path.dirname(__file__)
    model_dir = os.path.join(base_dir, "models", "unimernet_tiny")
    checkpoint = os.path.join(model_dir, "unimernet_tiny.pth")
    return FormulaRecognizer(model_dir, checkpoint)


def run_single(image_path: str):
    recognizer = load_model()
    print(recognizer.predict(image_path))


def run_server():
    """常驻进程：stdin 收图片路径，stdout 返结果"""
    # 告知父进程模型就绪
    recognizer = load_model()
    print("READY", flush=True)

    for line in sys.stdin:
        path = line.strip()
        if not path or path == "__EXIT__":
            break
        try:
            result = recognizer.predict(path)
            print(result, flush=True)
        except Exception as e:
            print(f"ERROR:{e}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_single(sys.argv[1])
    else:
        run_server()
