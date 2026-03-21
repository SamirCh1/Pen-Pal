import pygame
from pygame.locals import QUIT, KEYDOWN


import time
import json

from vectorise import PixelGraph, vectorise

from process_image import get_skeleton
import cv2

WHITE = (255, 255, 255)
BLACK = (0,0,0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)



def render_skeleton(screen, skeleton, colour):
    for x in range(skeleton.shape[1]):
        for y in range(skeleton.shape[0]):
            if skeleton[y][x]:
                pygame.draw.line(screen, colour, (x,y), (x,y), 1)

def render_points(screen, pixels, colour):
    for px in pixels:
        pygame.draw.line(screen, colour, px.dom.pos, px.dom.pos, 1)

def render_segments(screen, segments, colour):
    for segment in segments:
        for px in segment:
            a, b = px
            pygame.draw.line(screen, colour, a, b, 3)

def render(screen, graph: PixelGraph, segments: list, skeleton):
    screen.fill(BLACK)
    render_segments(screen, segments, WHITE)
    render_skeleton(screen, skeleton, RED)
    # render_points(screen, graph.segment_ends, RED)


def main():
    # modify file name as needed
    image = cv2.imread("images/handwritten.jpeg")
    # image = cv2.imread("images/test3.jpg")

    epsilon = 0.9

    dimensions = tuple(reversed(image.shape[0:2]))
    pygame.init()
    screen = pygame.display.set_mode(dimensions)


    run = True
    while run:
        skeleton = get_skeleton(image)
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False
            if event.type == KEYDOWN:
                if event.key ==  pygame.K_MINUS:
                    epsilon -= 0.1
                    if epsilon < 0:
                        epsilon = 0.0
                else:
                    epsilon += 0.1
                print(f"epsilon = {epsilon}")

        # skeleton = get_skeleton(image)
        current = time.time()
        graph, segments = vectorise(skeleton, epsilon)
        print(f"vectorisation done in {time.time() - current} seconds")
        print(f"{sum(len(seg) for seg in segments)} lines")


        render(screen, graph, segments, skeleton)

        pygame.display.update()

        current = time.time()

    pygame.quit()

if __name__ == "__main__":
    main()
