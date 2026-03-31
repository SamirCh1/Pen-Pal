from cv2.typing import MatLike
import numpy as np
import cv2
# from matplotlib import pyplot as plt
# from process_image import extract_paper

"""
    HOW IT COULD WORK
        find four largest contours containing significant brown (area1)
        find four largest contours within area1 (area2)
"""


def find_pins(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 3)

    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # return thresh

    blur = cv2.GaussianBlur(thresh, (7,7), 3)
    # return blur

    _, thresh = cv2.threshold(blur, 90, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) <= 80: # Ignore very small noise
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        if (max(w, h) / min(w, h) > 1.5):# or w<20 or h<20:
            continue

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return image




def main():
    # cap = cv2.VideoCapture(1)
    # frame = cap.read()
    image = cv2.imread("test1.jpg")

    if image is None:
        return

    paper = find_pins(image)
    if paper is None:
        return
    # paper = get_black_areas(image)
    cv2.imshow('image', paper)
    cv2.waitKey(0)
    cv2.destroyAllWindows()




if __name__ == "__main__":
    main()
