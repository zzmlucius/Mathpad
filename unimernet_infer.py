"""UniMERNet 推理脚本 - 接收图片路径，输出 LaTeX"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import torch
from PIL import Image
from omegaconf import OmegaConf

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from unimernet.models.unimernet.unimernet import UniMERModel
from unimernet.processors import load_processor
import unimernet

PKG_DIR = os.path.dirname(unimernet.__file__)


class FormulaRecognizer:
    """数学公式识别器"""

    def __init__(self, model_dir: str, checkpoint: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 加载模型默认配置，手动覆盖路径
        model_cfg = OmegaConf.load(
            os.path.join(PKG_DIR, "configs", "models", "unimernet_base.yaml")
        )
        model_cfg = model_cfg.model
        model_cfg.tokenizer_config.path = model_dir
        model_cfg.pretrained = checkpoint
        model_cfg.model_name = model_dir
        model_cfg.model_config.model_name = model_dir

        # 静默加载模型（抑制内部print）
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                self.model = UniMERModel.from_config(model_cfg).to(self.device)
                self.model.load_checkpoint(checkpoint)
            finally:
                sys.stdout = old_stdout
        self.model.eval()

        # 图像预处理器
        self.vis_processor = load_processor(
            "formula_image_eval",
            {"name": "formula_image_eval", "image_size": [192, 672]},
        )

    def predict(self, image_path: str) -> str:
        """识别图片中的公式，返回 LaTeX 字符串"""
        raw_image = Image.open(image_path).convert("RGB")
        image = self.vis_processor(raw_image).unsqueeze(0).to(self.device)
        output = self.model.generate({"image": image})
        return output["pred_str"][0]


def main():
    if len(sys.argv) < 2:
        print("Usage: python unimernet_infer.py <image_path>")
        sys.exit(1)

    base_dir = os.path.dirname(__file__)
    model_dir = os.path.join(base_dir, "models", "unimernet_tiny")
    checkpoint = os.path.join(model_dir, "unimernet_tiny.pth")

    recognizer = FormulaRecognizer(model_dir, checkpoint)
    result = recognizer.predict(sys.argv[1])
    print(result)


if __name__ == "__main__":
    main()
