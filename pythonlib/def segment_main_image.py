def segment_main_image(self):
        # Read the original image in grayscale
        original_image = Image.open(io.BytesIO(self.image_bytes)).convert('L')
        rgb_image = original_image.convert('RGB')
        rgb_array = np.array(rgb_image)
        gray_image = np.array(original_image)
        
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

            # Convert cropped image to NumPy array
            cropped_np_array = np.array(inverted_segment_cropped)
            cropped_bgr = cv2.cvtColor(cropped_np_array, cv2.COLOR_RGB2BGR)

            # Preprocess and perform OCR on the cropped image
            temp_results = self.preprocess_image(cropped_bgr)
            print('OCR Result:', temp_results)

            # Process OCR results and save segment images
            for result in temp_results:
                cv2.imwrite(segment_filename, segment_cropped)
                if result in segment_dictionary:
                    segment_dictionary[result].append(f"{self.image_name}_CC_{index}.png")
                else:
                    segment_dictionary[result] = [f"{self.image_name}_CC_{index}.png"]
            
            index += 1

        # Convert cmap labels to 8-bit unsigned integer
        cmap_labels_8u = cv2.convertScaleAbs(cmap(labels))
        print('cmap_labels_8u shape:', cmap_labels_8u.shape, 'dtype:', cmap_labels_8u.dtype)

        # Convert RGBA color map to RGB
        cmap_labels_rgb = cv2.cvtColor(cmap_labels_8u, cv2.COLOR_RGBA2RGB)
        print('cmap_labels_rgb shape:', cmap_labels_rgb.shape, 'dtype:', cmap_labels_rgb.dtype)

        # Overlay colored segments onto the original image
        overlay = cv2.addWeighted(rgb_array, 0.7, cmap_labels_rgb, 0.3, 0)
        print('overlay shape:', overlay.shape, 'dtype:', overlay.dtype)
        # Save the overlay image
        output_filename = f"{self.image_path}/segmentimages/{self.image_name}.png"
        cv2.imwrite(output_filename, overlay)

        return segment_dictionary