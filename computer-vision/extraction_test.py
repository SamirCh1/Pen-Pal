from cv2.typing import MatLike
import numpy as np
import cv2
from skimage.morphology import skeletonize
# from matplotlib import pyplot as plt
# from process_image import extract_paper
TL = (136/800, 26/480)
TR = (683/800, 22/480)
BL = (132/800, 418/480)
BR = (697/800, 413/480)

"""
    HOW IT COULD WORK
        find four largest contours containing significant brown (area1)
        find four largest contours within area1 (area2)
"""

def remove_corners(skeleton):
    height = skeleton.shape[0]
    width = skeleton.shape[1]

    curr_tl = (TL[0] * width, TL[1] * height)
    curr_tr = (TR[0] * width, TR[1] * height)
    curr_bl = (BL[0] * width, BL[1] * height)
    curr_br = (BR[0] * width, BR[1] * height)

    is_in_tl = lambda p: (p[0] - curr_tl[0])**2 < 50**2 and (p[1] - curr_tl[1])**2 < 50**2
    is_in_tr = lambda p: (p[0] - curr_tr[0])**2 < 50**2 and (p[1] - curr_tr[1])**2 < 50**2
    is_in_bl = lambda p: (p[0] - curr_bl[0])**2 < 50**2 and (p[1] - curr_bl[1])**2 < 50**2
    is_in_br = lambda p: (p[0] - curr_br[0])**2 < 50**2 and (p[1] - curr_br[1])**2 < 50**2

    lam_list = [is_in_tl, is_in_tr, is_in_bl, is_in_br]

    for x in range(width):
        for y in range(height):
            point = (x, y)
            for lam in lam_list:
                if lam(point):
                    skeleton[y][x] = False





def find_pins(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 3)
    # return blur
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 7, 2)
    canny = cv2.Canny(blur, 50, 100)
    skeleton = skeletonize(canny)
    remove_corners(skeleton)
    skeleton = skeleton * 255
    return skeleton.astype('uint8')

    blur = cv2.GaussianBlur(thresh, (7,7), 3)
    _, thresh = cv2.threshold(blur, 90, 255, cv2.THRESH_BINARY_INV)
    return thresh

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) <= 40: # Ignore very small noise
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        if (max(w, h) / min(w, h) > 1.5):# or w<20 or h<20:
            continue

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return image



def contours(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (11,11), 3)


    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    blur = cv2.GaussianBlur(thresh, (5, 5), 3)
    _, thresh = cv2.threshold(blur, 90, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) > 60: # Ignore very small noise
            x, y, w, h = cv2.boundingRect(cnt)

            if (max(w, h) / min(w, h) > 1.5):# or w<20 or h<20:
                continue

            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return image

def main():
    # cap = cv2.VideoCapture(1)
    # frame = cap.read()
    image = cv2.imread("board_test2.jpg")

    if image is None:
        return

    paper = find_pins(image)
    if paper is None:
        return
    cv2.imshow('image', paper)
    cv2.waitKey(0)
    cv2.destroyAllWindows()




if __name__ == "__main__":
    main()
