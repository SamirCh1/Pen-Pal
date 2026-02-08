# Source - https://stackoverflow.com/a/69816648
# Posted by Rabbid76
# Retrieved 2026-02-07, License - CC BY-SA 4.0

import pygame
from pygame.locals import QUIT
import numpy as np
import time

from process_image import *
import cv2
import potrace

WHITE = (255, 255, 255)
BLACK = (0,0,0)

# calculate location of point at t
def get_cubic_point(i, t, p0, p1, p2, p3):
    # i = 0 for x, 1 for y
    return (1-t)**3 * p0[i] + \
        3 * (1-t)**2 * t * p1[i] + \
        3 * (1-t) * t**2 * p2[i] + \
        t**3 * p3[i]

# render curve as series of lines between values of t
def render_cubic(screen, p0, p1, p2, p3):
    prev = p0
    for t in np.arange(0, 1, 0.01):
        point = (get_cubic_point(0, t, p0, p1, p2, p3), get_cubic_point(1, t, p0, p1, p2, p3))

        pygame.draw.line(screen, BLACK, point, prev, 1)
        prev = point
    pygame.draw.line(screen, BLACK, prev, p3, 1)


def main():

    start_time = time.time()
    print("SKELETONIZATION START")

    # modify file name as needed
    image = cv2.imread("images/test3.jpg")
    skeleton = full_processing_pipeline(image)

    print(f"SKELETONIZATION COMPLETED IN {round(time.time() - start_time, 3)} SECONDS")





    start_time = time.time()
    print("VECTORIZATION START")

    curve_list = vectorize(skeleton)

    print(f"VECTORIZATION COMPLETED IN {round(time.time() - start_time, 3)} SECONDS")

    dimensions = image.shape[0:2]

    pygame.init()
    screen = pygame.display.set_mode(dimensions)
    screen.fill(WHITE)

    pygame.display.update()

    print("RENDERING START")
    start_time = time.time()

    for curve in curve_list:
        # render each segment in curve
        for (p0, p1, p2, p3) in curve:
            render_cubic(screen, p0, p1, p2, p3)

            pygame.display.update() # can be moved outside loop, but here makes it look cooler

    print(f"RENDERING COMPLETED IN {round(time.time() - start_time, 3)} SECONDS")

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False

        # avoid wasting cpu cycles
        time.sleep(0.1)

    pygame.quit()

if __name__ == "__main__":
    main()
