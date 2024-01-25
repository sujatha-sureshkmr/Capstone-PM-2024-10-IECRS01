# Project Description

Welcome to the documentation for the Bolt Recognition System project. This project is aimed at developing a sophisticated pattern recognition system to detect and precisely locate bolts within images. The system's primary objective is to improve the efficiency and accuracy of a robot system used for bolt disassembly. We'll outline the key components, strategies, and methodologies that our group will employ to achieve this goal.

## Introduction

The Bolt Recognition System project focuses on enhancing the performance of the robot system used for bolt disassembly. To achieve this, we plan to establish a robust pattern recognition platform on Google Colab for a specialized model. While our initial choice for the pre-trained model is Yolo v8, we remain open to the possibility of adopting a customized model if the need arises. Our success metrics will revolve around achieving faster object segmentation and improved recognition accuracy.

## Image Distortion Correction

The existing robot system employs a specialized model to detect targets and calculate their physical coordinates. However, the use of significant system resources, particularly GPU resources, has room for improvement. We aim to develop an image distortion correction algorithm (A to A+ function) to enhance image quality. This enhancement, not mandated by Company-A but pursued for improved precision, will result in more accurate system output coordinates. Consequently, the robot system can respond more swiftly, reducing the cycle time for bolt disassembly.

## Preprocessing and Learning Strategies

To boost learning efficiency, our approach involves preprocessing raw images by cropping them into smaller images for key feature learning by the pre-trained model. Subsequently, we will transition to training with larger backgrounds until full-size images are utilized. This method allows the model to learn key features early in the training, followed by gradual adaptation to the target environment. Additionally, we will employ physical data augmentation techniques, including rotation, camera distance changes, camera angle variations, and illumination condition control, to enhance learning efficiency.

## Target Categorization

To enhance learning accuracy, we plan to categorize the target as Class-1, with the possibility of fine classification within Class-1 (e.g., Class-1a, Class-1b) for different bolt types. Noise targets from the background will be categorized as Class-2a, Class-2b, Class-2c, etc. The final output will merge as Class-1a, Class-1b, Class-1c, etc., into Class-1, which serves as the system target. Noise targets (Class-2a, Class-2b, Class-2c, etc.) designated for classification as noise bins will not be reported to the robot system.

## Bolt Outline Detection

Following object detection, we aim to detect the outline of the bolts using either the pattern recognition model or an alternative model, such as Fast-SAM or Yolo-seg. This step will yield a more precise center coordinate of the nuts, further enhancing the precision of the system.

## User Interface

To provide visibility into the pattern recognition process, we will design a user interface (UI) that displays raw images, final images after pattern recognition, and the detected object class, coordinates (x, y), confidence levels, and more. This UI will facilitate monitoring and debugging of the system.

## Integration and Testing

The entire pattern recognition model and Python code will be packaged as a sub-system with a designated API for seamless integration into Company-A's auto robot system. We will conduct final testing and evaluation to ensure the system meets the required performance standards.

Thank you for exploring our Bolt Recognition System project. We look forward to achieving improved efficiency and precision in the robot system, making bolt disassembly a faster and more accurate process. Please refer to the accompanying documentation for detailed information on implementation and usage.
