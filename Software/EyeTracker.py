import cv2
import numpy as np
from collections import deque
from typing import Tuple, Optional, List

class EyeTracker:

    def __init__(self, gazeBufferSize: int = 10, roiHistorySize: int = 60):
        """
        Initializes the EyeTracker.
        
        :param bufferSize: The number of frames to average for signal stabilization.
        :param roiHistorySize: Number of frames to keep for the ROI median filter. 
                                 ~60 frames is about 2 seconds at 30fps.
        """
        # Load OpenCV's pre-trained Haar cascade for eye detection
        #! cv2.data might not be recognized by your IDE, but it should work when you run the script
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eyeCascade = cv2.CascadeClassifier(eye_cascade_path)
        
        # Buffer for storing recent bounding boxes to calculate the median
        self.roiHistory = deque(maxlen=roiHistorySize)
        self.stableRoi = None
        self.eyeHFactor = 0.4
        self.pupilThreshold = 5

        # Circular buffer for signal stabilization (Moving Average)
        self.gazeBuffer = deque(maxlen=gazeBufferSize)
        self.stabilizedGaze = (0.0, 0.0)  # Initialize stabilized gaze vector
        self.normalizedGaze = (0.0, 0.0)  # Initialize normalized gaze vector
        
    def _updateRoi(self, grayFrame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detects the eye using Haar Cascades and applies a median filter over time."""
        # detectMultiScale finds the eye. this uses a high minSize to ignore background noise.
        eyes = self.eyeCascade.detectMultiScale(grayFrame, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        if len(eyes) > 0:
            # Assume the largest detection is the eye we want
            largestEye = max(eyes, key=lambda rect: rect[2] * rect[3])
            self.roiHistory.append(largestEye)
            
        if len(self.roiHistory) > 0:
            # Calculate the median of x, y, w, and h across the history buffer
            # This rejects short-term movements (looking around) but accepts long-term shifts (mask slipping)
            medX = int(np.median([r[0] for r in self.roiHistory]))
            medY = int(np.median([r[1] for r in self.roiHistory]))
            medW = int(np.median([r[2] for r in self.roiHistory]))
            medH = int(np.median([r[3] for r in self.roiHistory]))
            
            vertScaling = medH * self.eyeHFactor
            self.stableRoi = (medX, int(medY+vertScaling/2), medW, int(medH-vertScaling))
            return self.stableRoi
        
        return self.stableRoi  # Return the last stable ROI even if no new detection is found

    def preprocessFrame(self, frame: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int], Tuple[int, int]]:
        """
        Step 1: Image Acquisition & Preprocessing
        Automatically detects the eye, crops to it, and converts to grayscale.
        """
        # Haar cascade works better on grayscale images
        grayFull = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Dynamically find and update the eye ROI
        roi = self._updateRoi(grayFull)
        
        if roi:
            x, y, w, h = roi
            croppedGray = grayFull[y:y+h, x:x+w]
            offset = (x, y)
            anchorCropped = (w // 2, h // 2) 
        else:
            croppedGray = grayFull.copy()
            offset = (0, 0)
            h, w = croppedGray.shape
            anchorCropped = (w // 2, h // 2)
        
        # Slight Gaussian blur to reduce high-frequency noise from the sensor
        croppedGray = cv2.GaussianBlur(croppedGray, (5, 5), 0)
        
        return croppedGray, offset, anchorCropped

    def extractFeatures(self, grayFrame: np.ndarray) -> Tuple[Optional[Tuple[int, int]], np.ndarray]:
        """
        Step 2: Feature Extraction
        Isolates the pupil (darkest) and calculates its centroid.
        """
        # Dynamically determine intensity cutoffs using min pixel values
        minVal, _, _, _ = cv2.minMaxLoc(grayFrame)
        
        # Pupil is dark, so we look for pixels close to the minimum value
        #* 10 is arbitrary, we can mess with it if we want
        pupilThreshVal = minVal +  self.pupilThreshold

        _, pupilMask = cv2.threshold(grayFrame, pupilThreshVal, 255, cv2.THRESH_BINARY_INV)

        # Find centroid from the mask
        pupilCentroid = self._getLargestBlobCentroid(pupilMask)

        return pupilCentroid, pupilMask

    def _getLargestBlobCentroid(self, binaryMask: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Helper function to find the largest contour in a binary mask and calculate its centroid.
        """
        contours, _ = cv2.findContours(binaryMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        #TODO: if contour is really thin vertically, then we are blinking
            
        # Find the largest contour by area
        largestContour = max(contours, key=cv2.contourArea)
        
        # Calculate image moments to find the center (centroid) of the contour
        M = cv2.moments(largestContour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
            
        return None

    def estimateGaze(self, pupilPos: Tuple[int, int], anchorPos: Tuple[int, int]) -> Tuple[float, float]:
        """
        Step 3: Gaze Estimation
        Calculates the 2D difference vector between the pupil and the auto-detected anchor.
        """
        # dx, dy calculation. The center of the bounding box is the new anchor
        dx = pupilPos[0] - anchorPos[0]
        dy = pupilPos[1] - anchorPos[1]
        
        return float(dx), float(dy)

    def stabilizeSignal(self, rawGaze: Tuple[float, float]) -> Tuple[float, float]:
        """
        Step 4: Signal Stabilization
        Applies a moving average filter to the gaze buffer to eliminate anatomical jitter.
        """
        #! this function is implemented naively, but we can optimize it later
        #! if we see that it's necessary by avoiding the complete sum each time

        # Add the newest instantaneous gaze position to the circular buffer
        self.gazeBuffer.append(rawGaze)
        
        # Calculate the moving average for X and Y separately
        avgDx = sum(g[0] for g in self.gazeBuffer) / len(self.gazeBuffer)
        avgDy = sum(g[1] for g in self.gazeBuffer) / len(self.gazeBuffer)
        # median was too slow and not much better than average, so I kept average for simplicity
        # avgDx = float(np.median([g[0] for g in self.gazeBuffer]))
        # avgDy = float(np.median([g[1] for g in self.gazeBuffer]))

        return avgDx, avgDy

    def processFrame(self, frame: np.ndarray, 
                     showGray = False, showInstantGaze = False,
                     annotateFrame = False) -> Tuple[np.ndarray, Optional[Tuple[float, float]]]:
        """
        Main execution pipeline for a single frame. 
        Returns the annotated visualization frame and the stabilized gaze vector.
        If annotateFrame is True, it will draw the gaze vector and other visualizations on the frame.
            Turn to False to avoid the overhead of drawing
        """
        # 1. Preprocessing 
        gray, offset, anchorCropped = self.preprocessFrame(frame)
        
        # 2. Feature Extraction 
        pupilPos, pupilMask = self.extractFeatures(gray)
        
        # Visualization prep
        displayFrame = frame.copy()
        stabilizedGaze = None

        # Draw ROI box if active
        if self.stableRoi:
            x, y, w, h = self.stableRoi
            if annotateFrame: cv2.rectangle(displayFrame, (x, y), (x+w, y+h), (255, 0, 255), 2)

        if pupilPos and anchorCropped:
            # 3. Gaze Estimation (Using local cropped coordinates)
            rawGaze = self.estimateGaze(pupilPos, anchorCropped)
            
            # 4. Signal Stabilization
            stabilizedGaze = self.stabilizeSignal(rawGaze)

            # --- Visualization Drawing ---
            # Shift coordinates back to the original full frame for drawing
            pupilGlobal = (pupilPos[0] + offset[0], pupilPos[1] + offset[1])
            anchorGlobal = (anchorCropped[0] + offset[0], anchorCropped[1] + offset[1])
            stabilizedPupil = (int(anchorGlobal[0] + stabilizedGaze[0]), int(anchorGlobal[1] + stabilizedGaze[1]))

            if showGray: displayFrame[offset[1]:offset[1]+gray.shape[0], offset[0]:offset[0]+gray.shape[1]] = cv2.cvtColor(pupilMask, cv2.COLOR_GRAY2BGR)


            if annotateFrame:
                # Draw Pupil (Blue) and the new Anchor/Center (Red)
                if showInstantGaze: cv2.circle(displayFrame, pupilGlobal,     5, (255, 0, 0), -1)
                cv2.circle(displayFrame, stabilizedPupil, 3, (0, 255, 0), -1)
                cv2.circle(displayFrame, anchorGlobal,    3, (0, 0, 255), -1)
                
                # Draw difference vector line connecting anchor and pupil
                if showInstantGaze: cv2.line(displayFrame, anchorGlobal, pupilGlobal,     (255, 0, 255), 2)
                cv2.line(displayFrame, anchorGlobal, stabilizedPupil, (0, 255, 255), 2)

                displayFrame = cv2.flip(displayFrame, 1)
                
                # Display standardized gaze reading on screen
                cv2.putText(displayFrame, f"Gaze Vector (dx, dy): ({stabilizedGaze[0]:.1f}, {stabilizedGaze[1]:.1f})", 
                            (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
        self.stabilizedGaze = stabilizedGaze  # Store the latest stabilized gaze for external access
        if self.stableRoi:
            self.normalizedGaze = (stabilizedGaze[0] / (self.stableRoi[0] * 0.9), stabilizedGaze[1] / (self.stableRoi[1] * 0.9) if self.stableRoi else (0.0, 0.0))  # Normalize by ROI size if available
            # Cap normalized gaze to (-1, 1) range
            self.normalizedGaze = (
                max(-1.0, min(1.0, self.normalizedGaze[0])),
                max(-1.0, min(1.0, self.normalizedGaze[1]))
            )
        return displayFrame, stabilizedGaze