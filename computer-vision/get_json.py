# The purpose of this file is to test the vectorisation on the pi.
# Since the final version does not need pygame, we don't want to add
# more points of failure for debugging while testing on the pi.
# this does a single test on a complex image, outputting the time taken.
# The input image takes ~4 seconds to process on my laptop
import time
import json

from process_image import extract_paper, full_processing_pipeline, get_skeleton
import cv2


def main():
    # modify file name as needed
    image = cv2.imread("test6.jpg")

    start = time.time()

    paper = extract_paper(image)
    json_str = full_processing_pipeline(paper, on_paper=True)
    segments = json.loads(json_str)
    with open("smiley_drawn.json", "w") as file:
        json.dump(segments, file, indent=2)
    print(f"vectorisation done in {time.time() - start} seconds")




if __name__ == "__main__":
    main()
