from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_PATH = "PaddlePaddle/PaddleOCR-VL-1.5"

class PaddleOCREngine:
    def __init__(self, device=None, max_size=1200):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_size = max_size

        self.model = AutoModelForImageTextToText.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device).eval()

        self.processor = AutoProcessor.from_pretrained(MODEL_PATH)

    def _resize_image(self, image):
        w, h = image.size
        scale = self.max_size / max(w, h)
        if scale < 1:
            image = image.resize((int(w * scale), int(h * scale)))
        return image

    def extract_text(self, image_path, task="ocr", max_tokens=128):
        image = Image.open(image_path).convert("RGB")
        image = self._resize_image(image)

        prompt = {
            "ocr": "OCR:",
            "table": "Table Recognition:",
            "formula": "Formula Recognition:",
            "chart": "Chart Recognition:",
            "spotting": "Spotting:",
            "seal": "Seal Recognition:"
        }[task]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ]
            }
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=max_tokens)

        result = self.processor.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        )

        return result



# from ocr_engine import PaddleOCREngine

# ocr = PaddleOCREngine()

# text = ocr.extract_text("image.jpg")

# print(text)