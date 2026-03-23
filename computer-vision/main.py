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

# def get_sorted_contours(image: list[MatLike]):


def extract_paper(image: MatLike):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # lowerb = np.array([0, 0, 0])
    # upperb = np.array([40, 255, 255])
    # board_mask = cv2.inRange(hsv, lowerb, upperb)

    hsv_edges =  cv2.Canny(hsv, 50, 200)
    contours, hierarchy = cv2.findContours(hsv_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # print(sum([len(con) for con in contours]))
    contours_sorted = sorted(contours, reverse=True,  key=(lambda x: len(x)))
    new_image = cv2.drawContours(image, contours_sorted,0, (0,255,0), 3)

    return new_image
    return hsv_edges

def draw_corners(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    gray = np.float32(gray)
    dst = cv2.cornerHarris(gray,2,3,0.04)

    #result is dilated for marking the corners, not important
    # dst = cv2.dilate(dst,None)

    # Threshold for an optimal value, it may vary depending on the image.
    img[dst>0.01*dst.max()]=[0,0,255]
    return img

def get_black_areas(image):
    grey =

def main():
    # cap = cv2.VideoCapture(1)
    # frame = cap.read()
    image = cv2.imread("test3.jpg")

    if image is None:
        return
    print(image.shape)
    paper = draw_corners(image)
    # paper = extract_paper(image)
    # if paper is None:
        # return
    get_black_areas(paper)
    print(paper.shape)
    cv2.imshow('image', paper)
    cv2.waitKey(0)
    cv2.destroyAllWindows()




if __name__ == "__main__":
    main()
