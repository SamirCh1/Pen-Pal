import pygame
from pygame.locals import QUIT, KEYDOWN


import time
import json

from vectorise import PixelGraph, vectorise

from process_image import full_processing_pipeline, get_skeleton
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
                pygame.draw.circle(screen, colour, (x, y), 1)

def render_points(screen, pixels, colour):
    for px in pixels:
        pygame.draw.circle(screen, colour, px.dom.pos, 2) #line(screen, colour, px.dom.pos, px.dom.pos, 4)

# def render_segments(screen, segments, colour):
#     for segment in segments:
#         for px in segment:
#             a, b = px
#             pygame.draw.line(screen, colour, a, b, 3)

def render_segments(screen, segments, colour):
    for segment in segments:
        prev = segment[0]
        for current in segment:
            if current is prev:
                continue
            pygame.draw.line(screen, colour, prev, current, 3)
            prev = current

def render(screen, segments: list):
    screen.fill(WHITE)
    render_segments(screen, segments, BLACK)

def to_json(segments):
    string = json.dumps(segments)
    return string



def main():
    # modify file name as needed
    # image = cv2.imread("images/handwritten.jpeg")
    image = cv2.imread("images/test3.jpg")
    # image = cv2.imread("ina.png")

    epsilon = 0.9

    dimensions = tuple(reversed(image.shape[0:2]))
    pygame.init()
    # screen = pygame.display.set_mode(dimensions)
    screen = pygame.display.set_mode((1280, 720))

    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    run = True
    while run:
        for _ in range(5):
                cap.grab()
        success, frame = cap.retrieve()

        if not success:
            continue

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

        current = time.time()

        json_out = full_processing_pipeline(frame, on_paper=False)
        segments = json.loads(json_out)
        print(f"{sum([len(seg) for seg in segments])} lines")
        render(screen, segments)
        print(f"vectorisation done in {time.time() - current} seconds")
        pygame.display.update()

    cap.release()
    pygame.image.save(screen, "out.png")
    pygame.quit()

if __name__ == "__main__":
    main()
