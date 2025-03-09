from ben2 import BEN_Base
from PIL import Image
import torch


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

file = "./image.png" # input image

model = BEN_Base.from_pretrained("PramaLLC/BEN2")
model.to(device).eval()

image = Image.open(file)
foreground = model.inference(image, refine_foreground=False,) #Refine foreground is an extract postprocessing step that increases inference time but can improve matting edges. The default value is False.

foreground.save("./foreground.png")
