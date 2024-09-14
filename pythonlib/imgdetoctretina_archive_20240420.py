import easyocr
import io
import numpy as np
import torch
import torchvision
import cv2
from PIL import Image, ImageOps, ImageFilter
import matplotlib.pyplot as plt
from collections import Counter
import re


class retinaobjectvisionizer:
    def __init__(self, image_bytes, model):
        self.image_bytes = image_bytes
        self.model=model
    
    def ocr_image(self,image):
        cleaned_result=''
        reader = easyocr.Reader(['en'])
        upscale_factor = 2 # Increase this value if needed
        img = Image.fromarray(image)
        img = img.resize((img.width * upscale_factor, img.height * upscale_factor))
        img = np.array(img)
        result = reader.readtext(img)
        if not result:
            img = Image.fromarray(img)
            img = img.filter(ImageFilter.BLUR)
            img = img.resize((img.width * upscale_factor, img.height * upscale_factor))
            img = np.array(img)
            result = reader.readtext(img)
        #print(result)
        for detection in result:
            if detection:
                cleaned_result = re.sub(r'[^a-zA-Z0-9]', '', detection[1])
                #print('detection',detection[1])
                print('cleaned_result',cleaned_result)
        return cleaned_result

    def preprocess_image(self,model, image_bytes, threshold=0.5):
        ocr_detection = []
        image = Image.open(io.BytesIO(image_bytes)).convert('L')  # Convert to grayscale
        cropped_image = image
        inverted_image = ImageOps.invert(image)
        image_tensor = torchvision.transforms.ToTensor()(inverted_image).unsqueeze(0)
        with torch.no_grad():
            predictions = model(image_tensor)
            if len(predictions[0]['scores'].cpu()) ==0:
                print('no-predictions')
                result = self.ocr_image(np.array(inverted_image))
                if result:
                    ocr_detection.append(result)
            for box, score, label in zip(predictions[0]['boxes'].cpu(), predictions[0]['scores'].cpu(), predictions[0]['labels'].cpu()):
                if score >= threshold:
                    xmin, ymin, xmax, ymax = map(int, box.tolist())  
                    cropped_image = image.crop((xmin, ymin, xmax, ymax))
                    cropped_np_array = np.array(cropped_image)
                    cropped_bgr = cv2.cvtColor(cropped_np_array, cv2.COLOR_RGB2BGR)
                    result = self.ocr_image(cropped_bgr)
                    if result:
                        ocr_detection.append(result)
                        
        ocr_detection = list(Counter(ocr_detection))
        return ocr_detection
