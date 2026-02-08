import cv2
import numpy as np
import potrace

import time # for testing


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

def full_processing_pipeline(image):

    # paper = extract_paper(image)
    paper = image # temporary before proper implementation

    lines = extract_lines(paper)

    skeleton = skeletonize(lines)

    # curve_list = vectorize(skeleton)
    # return curve_list
    return skeleton


def extract_paper(image):
    # https://github.com/Akulaleelavathi/Extracting-a-Paper
    largest_contour = find_largest_contour(image)

    if largest_contour is None:
        print("Paper contour not found.")
        return image
    
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
        box = np.int0(box)
        ordered_points = order_points(box)
    
    # The dimensions of the new image (width and height) are computed based on the distances between the corners.
    # Compute the width and height of the new image based on the corners
    widthA = np.sqrt(((ordered_points[2][0] - ordered_points[3][0]) ** 2) + ((ordered_points[2][1] - ordered_points[3][1]) ** 2))
    widthB = np.sqrt(((ordered_points[1][0] - ordered_points[0][0]) ** 2) + ((ordered_points[1][1] - ordered_points[0][1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((ordered_points[1][0] - ordered_points[2][0]) ** 2) + ((ordered_points[1][1] - ordered_points[2][1]) ** 2))
    heightB = np.sqrt(((ordered_points[0][0] - ordered_points[3][0]) ** 2) + ((ordered_points[0][1] - ordered_points[3][1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Set destination points for the perspective transform
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(ordered_points, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # Resize the warped image to match the original image dimensions
    warped_resized = cv2.resize(warped, (image.shape[1], image.shape[0]))
    warped_coloured = cv2.cvtColor(warped_resized, cv2.COLOR_BGR2RGB)
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

    # # reduce noise in final output to save time tracing
    # blurred = cv2.GaussianBlur(adaptive, (5,5), 2)
    # _, threshold = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY)

    final = adaptive

    return final

def skeletonize(image):
    inverted = cv2.bitwise_not(image)
    thin = cv2.ximgproc.thinning(inverted)
    thin = cv2.bitwise_not(thin)
    final = thin
    return final

# convert skeletonized bitmap into series of curves
# # each curve contains a series of segments
# # each segment is a bezier curve
def vectorize(skeleton):

    #converts point from potrace's Point class to tuple
    normal_point = lambda point : (point.x, point.y)

    curve_list = []
    bmp = potrace.Bitmap(skeleton)
    path = bmp.trace(
        3, # min area of curve
        potrace.POTRACE_TURNPOLICY_BLACK, # seems like the most appropriate policy
        1.2, #alphamax: experiment with this
        True, #opticurve: set to True to minimize number of curves
        0.2 # tolerance: most likely should keep to default
        )
    curves = path.curves

    for curve in curves:
        # convert from potrace's Curve class to list of Bezier curves
        segments = []

        # each curve uses the end of the previous curve as its start
        last_end = curve.start_point
        for segment in curve.segments:

            if not segment.is_corner:
                segments.append((
                    normal_point(last_end),
                    normal_point(segment.c1),
                    normal_point(segment.c2),
                    normal_point(segment.end_point)))

                last_end = segment.end_point
        curve_list.append(segments)
    return curve_list


