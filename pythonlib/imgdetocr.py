import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import PIL
import torch
import torchvision
import os
import time
import xml.etree.ElementTree as ET
import cv2
from matplotlib.image import imsave
import easyocr
from PIL import Image
from io import BytesIO

# from google.colab.patches import cv2_imshow
from tabulate import tabulate
from torchvision import transforms


class objectvisionizer:
    def __init__(self, image_bytes, model, cpu):
        self.image_bytes = image_bytes

    def ocr_image(self, image):
        reader = easyocr.Reader(['en'])
        upscale_factor = 2  # Increase this value if needed
        img = image.copy()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

        img_resized = cv2.resize(img, None, fx=upscale_factor, fy=upscale_factor)
        result = reader.readtext(img_resized)
        return result

    def crop_and_infer_cv2(self, image_path, model, device):
        ocr_detection = np.array([])
        image = Image.open(BytesIO(image_path)).convert("RGB")
        width, height = image.size
        if width > 1200 or height > 800:
            num_segments_x = (width + 1199) // 1200
            num_segments_y = (height + 799) // 800
            segment_width = width // num_segments_x
            segment_height = height // num_segments_y
            results = []

            for i in range(num_segments_x):
                for j in range(num_segments_y):
                    left = i * segment_width
                    top = j * segment_height
                    right = min((i + 1) * segment_width, width)
                    bottom = min((j + 1) * segment_height, height)
                    cropped_image = image.crop((left, top, right, bottom))
                    transform = transforms.Compose([
                        transforms.ToTensor()
                    ])
                    img = transform(cropped_image).unsqueeze(0).to(device)
                    with torch.no_grad():
                        outputs = model(img)
                    results.append((left, top, outputs))

            stitched_image = np.array(image)
            detection_results = []
            
            if not results:
                result = self.ocr_image(stitched_image)
                for detection in result:
                    if detection:
                        ocr_detection = np.append(ocr_detection, detection[1])
            for left, top, outputs in results:
                boxes = outputs[0]['boxes'].cpu().numpy()
                labels = outputs[0]['labels'].cpu().numpy()
                scores = outputs[0]['scores'].cpu().numpy()

                for box, label, score in zip(boxes, labels, scores):
                    if score > 0.8:
                        box = box.astype(int)
                        xmin, ymin, xmax, ymax = box
                        detection_results.append([label, xmin, ymin, score])
                        cv2.rectangle(stitched_image, (xmin + left, ymin + top), (xmax + left, ymax + top),
                                      (0, 0, 255), 2)
                        label_text = f"Class: {label}, Score: {score:.2f}"
                        cv2.putText(stitched_image, label_text, (xmin + left, ymin + top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                        cropped_image = stitched_image[ymin + top:ymax + top, xmin + left:xmax + left]
                        result = self.ocr_image(cropped_image)
                        for detection in result:
                            if detection:
                                ocr_detection = np.append(ocr_detection, detection[1])

            print(tabulate(detection_results, headers=['Label', 'XMin', 'YMin', 'Score']))
            return ocr_detection
        else:
            transform = transforms.Compose([
                transforms.ToTensor()
            ])
            img = transform(image).unsqueeze(0).to(device)
            with torch.no_grad():
                outputs = model(img)
            image_np = np.array(image)
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            boxes = outputs[0]['boxes'].cpu().numpy()
            labels = outputs[0]['labels'].cpu().numpy()
            scores = outputs[0]['scores'].cpu().numpy()
            detection_results = []
            
            if len(boxes) == 0:
                result = self.ocr_image(image_np)
                for detection in result:
                    if detection:
                        ocr_detection = np.append(ocr_detection, detection[1])

            for box, label, score in zip(boxes, labels, scores):
                if score > 0.8:
                    box = box.astype(int)
                    xmin, ymin, xmax, ymax = box
                    detection_results.append([label, xmin, ymin, score])
                    cv2.rectangle(image_np, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
                    label_text = f"Class: {label}, Score: {score:.2f}"
                    cv2.putText(image_np, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),
                                2)
                    cropped_image = image_np[ymin + top:ymax + top, xmin + left:xmax + left]
                    result = self.ocr_image(cropped_image)
                    
                    for detection in result:
                        if detection:
                            ocr_detection = np.append(ocr_detection, detection[1])
                         

            print(tabulate(detection_results, headers=['Label', 'XMin', 'YMin', 'Score']))
            print(ocr_detection)
            return ocr_detection
