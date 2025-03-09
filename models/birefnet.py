from transformers import AutoModelForImageSegmentation
import torch

class BiRefNet:
    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, *model_args, **kwargs):
        model = AutoModelForImageSegmentation.from_pretrained(
            pretrained_model_name_or_path,
            trust_remote_code=True,
            *model_args,
            **kwargs
        )
        return model