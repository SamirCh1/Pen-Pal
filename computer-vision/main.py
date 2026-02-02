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


        # ret, frame = cap.read()
        #
        # cap.release()

        for i in range(1,4):

            frame = cv2.imread(f"test{i}.jpg")
            print(f"test{i}.jpg")

            paper = extract_paper(frame)

            lines = extract_lines(paper)

            skeleton = skeletonize(lines)



            # cv2.imshow('skeleton', skeleton)
            cv2.imwrite(f'out{i}_skeleton.png', skeleton)
            cv2.imwrite(f'out{i}_lines.png', lines)

        time.sleep(0.05)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



    cv2.destroyAllWindows()



if __name__ == "__main__":
    main()
