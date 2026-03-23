# The purpose of this file is to test the vectorisation on the pi.
# Since the final version does not need pygame, we don't want to add
# more points of failure for debugging while testing on the pi.
# this does a single test on a complex image, outputting the time taken.
# The input image takes ~4 seconds to process on my laptop
import time
import json

from process_image import full_processing_pipeline, get_skeleton
import cv2


def to_json(segments):
    string = json.dumps(segments)
    return string

def main():
    # modify file name as needed
    image = cv2.imread("images/smiley.png")
    # image = cv2.imread("ina.png")

    start = time.time()

    json_str = full_processing_pipeline(image, on_paper=False)
    segments = json.loads(json_str)
    with open("smiley.json", "w") as file:
        json.dump(segments, file, indent=2)
    print(f"{sum([len(seg) for seg in segments])} lines")
    print(f"vectorisation done in {time.time() - start} seconds")




if __name__ == "__main__":
    main()
