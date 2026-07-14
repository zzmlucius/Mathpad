"""UniMERNet 模型加载与推理"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import torch
from PIL import Image
from omegaconf import OmegaConf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
            old = sys.stdout
            sys.stdout = devnull
            try:
                self.model = UniMERModel.from_config(model_cfg).to(self.device)
                self.model.load_checkpoint(checkpoint)
            finally:
                sys.stdout = old
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
    model_dir = os.path.join(BASE_DIR, "models", "unimernet_tiny")
    checkpoint = os.path.join(model_dir, "unimernet_tiny.pth")
    return FormulaRecognizer(model_dir, checkpoint)
