# Source - https://stackoverflow.com/a/69816648
# Posted by Rabbid76
# Retrieved 2026-02-07, License - CC BY-SA 4.0

import pygame
from pygame.locals import *
import numpy as np
import time

from process_image import full_processing_pipeline
import cv2
import potrace

def scale_tuple(tpl, x):
    return (tpl[0] * x, tpl[1] * x)

def render_quadratic(screen, p0, p1, p2):
    for p in [p0, p1, p2]:
        pass
            # pygame.draw.circle(screen, (255, 255, 255), p, 5)
    for t in np.arange(0, 1, 0.002):
        px = p0[0]*(1-t)**2 + 2*(1-t)*t*p1[0] + p2[0]*t**2
        py = p0[1]*(1-t)**2 + 2*(1-t)*t*p1[1] + p2[1]*t**2
        pygame.draw.rect(screen, (255, 255, 0), (px, py, 1, 1))

def get_cubic_point(i, t, p0, p1, p2, p3):
    # i = 0 for x, 1 for y
    return (1-t)**3 * p0[i] + \
        3 * (1-t)**2 * t * p1[i] + \
        3 * (1-t) * t**2 * p2[i] + \
        t**3 * p3[i]

def render_cubic(screen, p0, p1, p2, p3):
    prev = p0
    for p in [p0, p1, p2, p3]:
        pass
        # pygame.draw.circle(screen, (255, 255, 255), p, 5)
    for t in np.arange(0, 1, 0.01):
        point = (get_cubic_point(0, t, p0, p1, p2, p3), get_cubic_point(1, t, p0, p1, p2, p3))

        # pygame.draw.rect(screen, (255, 0, 0), (px, py, 1, 1))
        pygame.draw.line(screen, (255, 0, 0), point, prev, 1)
        prev = point

def normal_point(point):
    return (point.x, point.y)


def vectorize(skeleton):
    curve_list = []
    bmp = potrace.Bitmap(skeleton)
    path = bmp.trace()
    curves = path.curves

    for curve in curves:
        segments = []
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

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 500))


    image = cv2.imread("images/test3.jpg")
    skeleton = full_processing_pipeline(image)
    curve_list = vectorize(skeleton)



    screen.fill(0)


    for curve in curve_list:
        for (p0, p1, p2, p3) in curve:
            render_cubic(screen, p0, p1, p2, p3)
    pygame.display.update()

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False

        time.sleep(0.02)

    pygame.quit()

if __name__ == "__main__":
    main()
