import numpy as np
import cv2
from threading import Timer
import time
from matplotlib import pyplot as plt

from process_image import *


def corner_detect(img):
    # gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)

    gray = img
    dst = cv2.cornerHarris(gray,5,1,0.04)
    #result is dilated for marking the corners, not important
    dst = cv2.dilate(dst,None)

    # Threshold for an optimal value, it may vary depending on the image.
    img[dst>0.01*dst.max()]=[0,0,255]

    return img

def mark_contours(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5,5), 5)

    edges = cv2.Canny(gray, 20, 20)

    contours, image = cv2.findContours(edges, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    img = cv2.drawContours(img, contours, -1, (0,255,0), 3)
    return img

def main():
    cap = cv2.VideoCapture(1)

    # frame = cv2.imread('test3.jpg')


    while True:

        # ret, frame = cap.read()

        # paper = frame

        # paper = extract_paper(frame)

        # lines = extract_lines(paper)
        #
        # skeleton = skeletonize(lines)

        skeleton = cv2.imread('test3_skeleton.png')

        vectorize(skeleton)

        cv2.imshow('OpenCV frame', paper)


        break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    main()
