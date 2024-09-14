# report purposes
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from imgdetoctretina import retinaobjectvisionizer

class segmentimage:
    def __init__(self, image):
        self.image = image

    def segmentmainimage(self,image):
        # Read the image
        #image = cv2.imread('img0-0.png')
        image = cv2.imread('img9-0.png')


        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Perform thresholding
        _, thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)


        # Perform dilation
        kernel = np.ones((15, 15), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=3)


        # Find connected components
        num_labels, labels = cv2.connectedComponents(dilated)

        # Create a colormap for segments
        cmap = ListedColormap(np.random.rand(num_labels, 3))


        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)

        # Create a blank image to draw colored segments
        colored_segments = np.zeros_like(image)

        i=0
        # Iterate through each segment
        for label in range(1, num_labels):
            # Create a mask for the segment
            segment_mask = labels == label
            
            # Generate a random color
            color = np.random.randint(0, 256, size=3)
            
            # Color the segment in the blank image
            colored_segments[segment_mask] = color
            
            segment_mask = labels == label
            
            # Find bounding box for the segment
            x, y, w, h = cv2.boundingRect(segment_mask.astype(np.uint8))
            
            # Crop the segment from the main image
            segment_cropped = np.zeros_like(image)
            segment_cropped[segment_mask] = image[segment_mask]
            segment_cropped = segment_cropped[y:y+h, x:x+w]
            
            # Generate a random color
            color = np.random.randint(0, 256, size=3)
            
            # Create a mask for the segment to apply the color
            mask = np.any(segment_cropped > 0, axis=-1)[:, :, np.newaxis]
            mask = np.repeat(mask, 3, axis=-1)
            
            # Add the color to the segment
            segment_colored = np.where(mask, color, segment_cropped).astype(np.uint8)
            
            cv2.imwrite(f"connected_components{i}.png", segment_colored)
            i=i+1
            
        # Overlay colored segments onto the original image
        overlay = cv2.addWeighted(image, 0.7, colored_segments, 0.3, 0)

        cv2.imwrite(f"Segmentation_UI.png", overlay)
