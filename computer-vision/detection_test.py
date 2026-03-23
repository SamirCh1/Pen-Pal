import detect_object as d_o
import cv2

# capture = cv2.VideoCapture(1)
# print(capture)
# if not capture.isOpened():
#     print('Unable to open camera')
#     exit(0)
# _, frame = capture.read()
# print('dimension: ' + (str)(frame.shape[1]) + ', ' + (str)(frame.shape[0]))

# detect_movement()
# run_analysis(1)
# detect_paper_video()

image1 = cv2.imread('t2.jpeg')
image2 = cv2.imread('t3.jpeg')
paper1 = d_o.detect_paper_frame(image1)
if paper1 is None: print("paper1 not found")
paper2 = d_o.detect_paper_frame(image2)
if paper2 is None: print("paper2 not found")
cv2.waitKey()
diff = d_o.detect_difference(paper1, paper2)
print('dimension: ' + (str)(diff.shape[1]) + ', ' + (str)(diff.shape[0]))
cv2.waitKey()

