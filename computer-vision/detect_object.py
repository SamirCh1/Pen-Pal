'''
1. user put paper in
2. detect paper and wait user remove obstruction
3. wait for drawing -> detect difference
    if is a line: vectorize
    else: wait
'''
import cv2
import numpy as np
import time

def process_image(image):
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image_gray

def detect_difference(image1: cv2.typing.MatLike, image2: cv2.typing.MatLike):
    diff = cv2.absdiff(image1, image2)
    #  dilation expands or thickens regions of interest in an image.
    dilated = cv2.dilate(diff,cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3)),iterations = 2)
    cv2.imshow('Diff', diff)
    cv2.imshow('Dilated diff', diff)

def detect_paper():
    while True:
        _, frame = capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 9)

        # _, thresh = cv2.threshold(blur, 255/3, 255, cv2.THRESH_TOZERO)
        # elements = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        # dilate = cv2.dilate(thresh, elements)
        # erode = cv2.erode(thresh, elements)
        # blur_edge = dilate-erode
        # cv2.imshow('blur edge', blur_edge)
        # enforced_edge = cv2.dilate(blur_edge, elements)
        # _, enforced_edge = cv2.threshold(enforced_edge, 9, 255, cv2.THRESH_BINARY)
        # cv2.imshow('enforced edge', enforced_edge)
        # edge = cv2.ximgproc.thinning(enforced_edge)
        # cv2.imshow('edge', edge)

        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 3)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)))
        cv2.imshow('morph', morph)

        contours = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        show_contours = frame.copy()
        cv2.drawContours(show_contours, contours, 0, (0,255,0), thickness=5)
        cv2.imshow('show contours', show_contours)

        rect_contour = None
        warp_map = None
        a4_width = 594
        a4_height = 420
        dimension = np.array([
                             [0,0],
                             [a4_width-1, 0],
                             [a4_width-1, a4_height-1],
                             [0, 840-1]], dtype='float32')

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            peri = cv2.arcLength(contour, True)
            appr = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(appr) == 4 and cv2.isContourConvex(appr):
                if cv2.contourArea(appr) > (frame.shape[0] * frame.shape[1] * 0.5):
                    rect_contour = appr
                    break
        if rect_contour is not None:
            show_rect_contour = frame.copy()
            cv2.drawContours(show_rect_contour, [rect_contour], 0, (0,0,255), thickness=7)
            cv2.imshow('show rectangle contours', show_rect_contour)
            rect = order_rect(rect_contour.reshape(4,2))
            warp_map = cv2.getPerspectiveTransform(rect, dimension)
        if warp_map is not None:
            warped = cv2.warpPerspective(frame, warp_map, (a4_width, a4_height))
            cv2.imshow("warped", warped)

        cv2.waitKey((int)(1000/60))

def order_rect(rect):
    res = np.ndarray((4,2), dtype='float32')
    xy_sum = rect.sum(axis=1)
    res[0] = rect[np.argmin(xy_sum)]
    res[2] = rect[np.argmax(xy_sum)]

    xy_diff = np.diff(rect, axis=1)
    res[1] = rect[np.argmin(xy_diff)]
    res[3] = rect[np.argmax(xy_diff)]
    return res


def detect_movement():
    changed = False
    frame_rate = 15
    prev = 0

    t = time.time()
    now = t
    while now - t <= 5:
        now = time.time()
        print(now)
        _, frame = capture.read()
        foreground_mask = back_sub.apply(frame)
        cv2.waitKey((int)(1000/60))

    _, past_output = capture.read()
    past_output = cv2.cvtColor(past_output, cv2.COLOR_BGR2GRAY)
    if past_output is None:
        raise Exception("No frame found")
    while True:
        _, frame = capture.read()
        cv2.imshow('Frame', frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        foreground_mask = back_sub.apply(frame)
        background_image = back_sub.getBackgroundImage(frame)

        # cv2.imshow('Foreground mask', foreground_mask)
        # cv2.imshow('background image', background_image)
        # threshold if it is bigger than 240 pixel is equal to 255 if smaller pixel is equal to 0
        # create binary image , it contains only white and black pixels
        ret , treshold = cv2.threshold(foreground_mask.copy(), 120, 255,cv2.THRESH_BINARY)
        
        #  dilation expands or thickens regions of interest in an image.
        dilated = cv2.dilate(treshold,cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3)),iterations = 2)
        cv2.imshow('dilated', dilated)
    
        average = dilated.mean()/255
        print(average)
        change_threshold = 0.08
        reset_threshold = 0.03
        if average > change_threshold and not changed:
            print("changed")
            changed = True
        if average < reset_threshold and changed:
            _, current_output = capture.read()
            current_output = cv2.cvtColor(current_output, cv2.COLOR_BGR2GRAY)
            detect_difference(past_output, current_output)
            past_output = current_output
            changed = False

        key = cv2.waitKey((int)(1000/frame_rate))
        if key == 'q' or key == 27:
            break

def detect_object(diff):
    
    return


def run_analysis(index):
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print("Error opening video")

    while(cap.isOpened()):
        status, frame = cap.read()
        if status:
            cv2.imshow('frame', frame)
            # do_stuff_with_frame(frame)
        key = cv2.waitKey(25)
        if key == ord('q'):
            break

# image1 = cv2.imread('test3.jpg')
# image2 = cv2.imread('test3_alt.jpg')
# if image1 is not None and image2 is not None:
#     detect_difference(image1, image2)

capture = cv2.VideoCapture(1)
print(capture)
if not capture.isOpened():
    print('Unable to open camera')
    exit(0)

# back_sub = cv2.createBackgroundSubtractorKNN()
back_sub = cv2.createBackgroundSubtractorMOG2()
# detect_movement()

# run_analysis(1)
detect_paper()
