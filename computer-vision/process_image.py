import cv2
import skimage.morphology as morph
import numpy as np
from vectorise import vectorise
import json

board_hsv = 0

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

def get_current_frame(cap: cv2.VideoCapture):
    image = None
    while image is None:
        for _ in range(5):
            cap.grab()
        success, frame = cap.retrieve()
        if not success:
            continue

        image = extract_paper(image)
    return image


def full_processing_pipeline(image, on_paper=True):

    lines = extract_lines_blur(image, 3, 10)

    skeleton = skeletonize(lines)

    _, segment_list = vectorise(skeleton)

    if on_paper:
        segment_list = to_a4(skeleton, segment_list)

    segments_json = json.dumps(segment_list)

    return segments_json

# temporary function for testing vectorisation
def get_skeleton(image):
    paper = image

    lines = extract_lines_blur(paper, 5, 128)

    skeleton = skeletonize(lines)
    return skeleton

def to_a4(skeleton, segment_list):
    # a4_w, a4_h = 210, 297
    a4_w, a4_h = 297, 210
    img_h, img_w = tuple(skeleton.shape[0:2])

    #both should be 4
    w_ratio = a4_w/img_w
    h_ratio = a4_h/img_h

    segments = []
    for seg in segment_list:
        segment = []
        for p in seg:
            x,y = p
            segment.append([x*w_ratio, (img_h-y)*h_ratio])
        segments.append(segment)

    return segments

def extract_paper(image):
    # https://github.com/Akulaleelavathi/Extracting-a-Paper
    largest_contour = find_largest_contour(image)

    if largest_contour is None:
        print("Paper contour not found.")
        return None

    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)

    # Check if we have four points (i.e., four corners)
    if len(approx) == 4:
        # Extract the four points
        ordered_points = order_points(approx.reshape(4, 2))
    else:
        # If not, use the minimum enclosing rectangle
        # https://theailearner.com/tag/cv2-minarearect/
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        ordered_points = order_points(box)


    ## 4x a4 proportions
    paper_w = 1189
    paper_h = 841
    # paper_w = 841
    # paper_h = 1189

    # Set destination points for the perspective transform
    dst = np.array([
        [0, 0],
        [paper_w - 1, 0],
        [paper_w - 1, paper_h - 1],
        [0, paper_h - 1]], dtype="float32")

    # Compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(ordered_points, dst)
    warped = cv2.warpPerspective(image, M, (paper_w, paper_h))

    # Resize the warped image to match the original image dimensions
    warped_resized = cv2.resize(warped, (paper_w, paper_h))
    # warped_coloured = cv2.cvtColor(warped_resized, cv2.COLOR_BGR2RGB)
    warped_coloured = warped_resized
    return warped_coloured

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def find_largest_contour(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hsv = cv2.GaussianBlur(hsv, (5,5), 2)

    lower = np.array([20, 100, 0])
    upper = np.array([340, 255, 255])

    red = cv2.inRange(hsv, lower, upper)
    # canny =cv2.Canny(grey, )

    contours, hierarchy = cv2.findContours(image=red, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
    sortedContours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

    if len(contours) > 1:
        return sortedContours[1]
    else:
        return None


def extract_lines(image, blockSize = 13):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 2)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, 2)

    # reduce noise in final output to save time tracing
    # blurred = cv2.GaussianBlur(adaptive, (5,5), 2)
    # _, threshold = cv2.threshold(blurred, 128, 255, cv2.THRESH_BINARY)

    final = adaptive

    return final

def extract_lines_blur(image, k, thres, blockSize = 13):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 2)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, 2)

    # reduce noise in final output to save time tracing
    if k % 2 == 0:
        k -= 1
    blurred = cv2.GaussianBlur(adaptive, (k,k), 2)
    _, threshold = cv2.threshold(blurred, thres, 255, cv2.THRESH_BINARY)

    final = threshold


    return final

def skeletonize(image):
    inverted = cv2.bitwise_not(image)
    thin = morph.skeletonize(inverted)
    return thin
