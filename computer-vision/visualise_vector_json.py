from numpy import average
import pygame
from pygame.locals import QUIT, KEYDOWN

import time
import json

from vectorise import PixelGraph, vectorise

from process_image import extract_paper, full_processing_pipeline, get_skeleton
import cv2

WHITE = (255, 255, 255)
BLACK = (0,0,0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)




def render_segments(screen, segments, colour):
    for segment in segments:
        prev = segment[0]
        for current in segment:
            if current is prev:
                continue
            pygame.draw.line(screen, colour, prev, current, 1)
            prev = current

def render(screen, segments: list):
    screen.fill(WHITE)
    render_segments(screen, segments, BLACK)


def main():
    pygame.init()
    screen = pygame.display.set_mode((500,500))

    with open("smiley_drawn.json", "r") as f:
        segments = json.load(f)

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False

        render(screen, segments)
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
