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
from matplotlib.colors import ListedColormap

class retinaobjectvisionizer:
    def __init__(self, model, image_bytes, image_name, image_path):
        self.model = model
        self.image_bytes = image_bytes
        self.image_name = image_name.split(".")[0]
        self.image_path = image_path
        self.image = self.convert_image(image_bytes)

    def convert_image(self, image_bytes):
        # Convert image bytes to grayscale and invert it
        image = Image.open(io.BytesIO(image_bytes)).convert('L')
        inverted_image = ImageOps.invert(image)
        return inverted_image

    def segment_main_image(self):
        # Read the original image in grayscale
        print('segment_main_image')
        original_image = Image.open(io.BytesIO(self.image_bytes)).convert('L')
        rgb_image = original_image.convert('RGB')
        rgb_array = np.array(rgb_image)
        gray_image = np.array(original_image)
        print('colored_segments')
        colored_segments = np.zeros_like(rgb_array)
        # Perform thresholding using Otsu's method
        _, thresholded_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Perform dilation to enhance connected components
        kernel = np.ones((15, 15), np.uint8)
        dilated_image = cv2.dilate(thresholded_image, kernel, iterations=3)

        # Find connected components
        num_labels, labels = cv2.connectedComponents(dilated_image)

        # Create a color map for the segments
        cmap = ListedColormap(np.random.rand(num_labels, 3))
        
        # Find connected components with stats and centroids
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated_image, connectivity=8)

        # Initialize a dictionary to store segment information
        segment_dictionary = {}
        index = 0
        
        # Iterate through each segment and process it
        for label in range(1, num_labels):
            # Create a mask for the segment
            segment_mask = labels == label
            # Generate a random color
            
            # Find bounding box for the segment
            x, y, w, h = cv2.boundingRect(segment_mask.astype(np.uint8))

            # Crop the segment from the main image
            segment_cropped = np.zeros_like(rgb_array)
            segment_cropped[segment_mask] = rgb_array[segment_mask]
            segment_cropped = segment_cropped[y:y + h, x:x + w]
    
            # Perform OCR on the cropped segment
            segment_cropped_image = Image.fromarray(segment_cropped)
            inverted_segment_cropped = ImageOps.invert(segment_cropped_image)
            segment_filename = f"{self.image_path}/segmentimages/{self.image_name}_CC_{index}.png"
            #segment_filename_display = f"{self.image_path}/segmentimagesdisplay/{self.image_name}_CC_{index}.png"
            # Convert cropped image to NumPy array
            cropped_np_array = np.array(inverted_segment_cropped)
            cropped_bgr = cv2.cvtColor(cropped_np_array, cv2.COLOR_RGB2BGR)

            # Generate a random color
            color = np.random.randint(0, 256, size=3)
            
            # Create a mask for the segment to apply the color
            mask = np.any(segment_cropped > 0, axis=-1)[:, :, np.newaxis]
            mask = np.repeat(mask, 3, axis=-1)
            
            # Add the color to the segment
            segment_colored = np.where(mask, color, segment_cropped).astype(np.uint8)

            colored_segments[segment_mask] = color

            # Preprocess and perform OCR on the cropped image
            temp_results = self.preprocess_image(segment_cropped)
            print('OCR Result:', temp_results)

            # Process OCR results and save segment images
            for result in temp_results:
                cv2.imwrite(segment_filename, segment_colored)
                #cv2.imwrite(segment_filename_display, segment_colored)
                if result in segment_dictionary:
                    segment_dictionary[result].append(f"{self.image_name}_CC_{index}.png")
                else:
                    segment_dictionary[result] = [f"{self.image_name}_CC_{index}.png"]
            
           

            # Convert cmap labels to 8-bit unsigned integer
            cmap_labels_8u = cv2.convertScaleAbs(cmap(labels))

            # Convert RGBA color map to RGB
            cmap_labels_rgb = cv2.cvtColor(cmap_labels_8u, cv2.COLOR_RGBA2RGB)

            # Overlay colored segments onto the original image
            overlay = cv2.addWeighted(rgb_array, 0.7, colored_segments, 0.3, 0)
            print('overlay shape:', overlay.shape, 'dtype:', overlay.dtype)
            # Save the overlay image
            output_filename = f"{self.image_path}/segmentimages/{self.image_name}.png"
            cv2.imwrite(output_filename, overlay)
            cv2.imwrite(f"{self.image_path}/{self.image_name}.png", overlay)
            index += 1
        return segment_dictionary

    def process_string(self, input_string):
        # Check if the string is alphanumeric
        #print('step 2AA',input_string)
        input_string = input_string.replace('I', '1')
        if input_string.isdigit():
            #print('step 2AC isdigit',len(input_string))
            # Convert the string to an integer
            num_value = int(input_string)
            # Check if the number is between 0 and 15
            if not (1 <= num_value <= 50):
                #print('step 2AD not (1 <= num_value <= 50):',num_value)
                return ""
        elif input_string.isalnum():
            #print('step 2AB isalnum',len(input_string))
            # If alphanumeric and length is greater than 1, make the string blank
            
                
            if len(input_string) > 1:
                return ""

        # Check if the string contains only numeric characters
        

        # If the string passes the conditions, return the input string
        return input_string

    def ocr_image(self, image):
        cleaned_result = ''
        reader = easyocr.Reader(['en'])
        upscale_factor = 2  # Increase this value if needed
        
        img = Image.fromarray(image)
        img = img.resize((img.width * upscale_factor, img.height * upscale_factor))
        img = np.array(img)
        #print('step 2A')
        # Perform OCR on the image
        result = reader.readtext(img)
        #print('step 2B',result)
        # If no results, apply blur and try OCR again
        if not result:
            img = Image.fromarray(img)
            img = img.filter(ImageFilter.BLUR)
            img = img.resize((img.width * upscale_factor, img.height * upscale_factor))
            img = np.array(img)
            result = reader.readtext(img)
            #print('step 2C',result)
            print('OCR result after blur:', result)
        if not result:
            print('No detection after 2nd time', result)
        
        # Clean and process the OCR results
        accuracy = 0
        cleaned_result = ""
        for detection in result:
            #print('step 2D',detection,detection[1],detection[2])
            if len(str(detection[1])) == 4:
                second_element = detection[1]
                # Extract the 2nd and 3rd characters
                detection = (detection[0], second_element[1:3], detection[2])
            if detection and detection[2] >= accuracy:
                cleaned_result_main = re.sub(r'[^a-zA-Z0-9]', '', detection[1])
                result_second = self.process_string(cleaned_result_main)
                if result_second == '':
                    cleaned_result = cleaned_result
                    accuracy = detection[2]
                else: 
                    cleaned_result = result_second
                    accuracy = detection[2]

                #print('step 2E',cleaned_result_main)
                #print('step 2F',cleaned_result)

        print('Cleaned OCR result:', cleaned_result)
        return cleaned_result

    def preprocess_image(self, image_bytes=None, threshold=0.5):
        ocr_detection = []

        if image_bytes is None:
            inverted_image = self.image if isinstance(self.image, Image.Image) else None
            if not inverted_image:
                raise ValueError("Invalid type for 'image'. Expected a PIL Image object.")
        else:
            inverted_image = Image.fromarray(image_bytes)

        image_tensor = torchvision.transforms.ToTensor()(inverted_image).unsqueeze(0)

        with torch.no_grad():
            #print('step 1 ocr_image')
            predictions = self.model(image_tensor)
            if len(predictions[0]['scores'].cpu()) == 0:
                #print('step 2 ocr_image')
                result = self.ocr_image(np.array(inverted_image))
                #print('step 2 ',result)
                if result:
                    ocr_detection.append(result)

            for box, score, label in zip(predictions[0]['boxes'].cpu(), predictions[0]['scores'].cpu(), predictions[0]['labels'].cpu()):
                if score >= threshold:
                    #print('step 3 ocr_image')
                    xmin, ymin, xmax, ymax = map(int, box.tolist())
                    cropped_image = inverted_image.crop((xmin, ymin, xmax, ymax))
                    cropped_np_array = np.array(cropped_image)
                    cropped_bgr = cv2.cvtColor(cropped_np_array, cv2.COLOR_RGB2BGR)
                    
                    try:
                        #print('step 4 ocr_image')
                        result = self.ocr_image(cropped_bgr)
                        print(result)
                    except cv2.error as e:
                        print(f"Error in ocr_image: {e}")
                    
                    if result:
                        ocr_detection.append(result)

        # Deduplicate and return OCR detection results
        ocr_detection = list(Counter(ocr_detection))
        print('OCR detection results:', ocr_detection)
        return ocr_detection
