import cv2
import potrace

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
# find 4 coordinates of the corners of the paper and remove all components outside of it
# for now, assume flat a4 on contrasting surface
def extract_paper(image):
    final = image
    return final;

# find
def extract_lines(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    blurred = cv2.GaussianBlur(gray, (5,5), 2)

    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)


    final = adaptive

    return final;

def skeletonize(image):
    image = cv2.ximgproc.thinning(image, image, cv2.ximgproc.THINNING_GUOHALL)
    # image = cv2.ximgproc.thinning(image)
    final = image
    return final;

def vectorize(image):
    bmp = potrace.Bitmap(image)
    final = image
    return final
