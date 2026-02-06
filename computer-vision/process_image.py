import cv2
import numpy as np


"""
Steps in image processing pipeline:
    1. extract paper from image
    2. turn into binary format to extract lines
        - adaptive thresholding
        - noise removal
    3. skeletonize image to get strokes
        - remove 'branches' in skeleton
    4. vectorise skeletonized image
        - convert to series of lines
        - convert sequential lines into curves
    5. normalise vector to correct proportions and angle
"""

#TODO
# find coordinates of 3-4 corners of the paper and remove all components outside of it
# for demo 1, assume flat a4 on contrasting surface
def extract_paper(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hsv = cv2.GaussianBlur(hsv, (5,5), 2)

    lower_red = np.array([20, 100, 0])
    upper_red = np.array([340, 255, 255])

    red = cv2.inRange(hsv, lower_red, upper_red)

    contours, hierarchy = cv2.findContours(image=red, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)

    sortedContours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

    paper_contour = []

    if len(contours) > 1:
        paper_contour = sortedContours[1]
    else:
        return image

    x, y, w, h = cv2.boundingRect(paper_contour)
    img = cv2.drawContours(image, [paper_contour], -1, (0,255,0), 3)

    final = img
    return final;


def extract_lines(image, blockSize = 13):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 2)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, 2)
    final = adaptive

    return final;

def skeletonize(image):
    inverted = cv2.bitwise_not(image)
    thin = cv2.ximgproc.thinning(inverted)
    final = thin
    return final;

def vectorize(image):
    final = image
    return final
