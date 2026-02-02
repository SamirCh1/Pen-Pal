import numpy as np
import cv2
from threading import Timer
import time
from matplotlib import pyplot as plt

from process_image import *


def main():
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while True:


        ret, frame = cap.read()



        paper = extract_paper(frame)

        lines = extract_lines(paper)

        skeleton = skeletonize(lines)


        cv2.imshow('skeleton', skeleton)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    main()
