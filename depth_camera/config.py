import cv2

YOLO_BBOX_MODEL_PATH   = "depth_camera//models//yolov8n.pt"
YOLO_SEG_MODEL_PATH   = "depth_camera//models//yolov8n-seg.pt"
YOLO_GRIPPER_MODEL_PATH   = "depth_camera//models//yolo8n-gripper.pt"
YOLO_MODEL_CONFIG = "depth_camera//models//config.yaml"
YOLO_SAM_MODEL_PATH = "depth_camera//models//sam_b.pt"
YOLO_BARCODE_MODEL_PATH = "depth_camera//models//yolo8n-barcode.pt"
YOLO_BARCODE_MODEL_PATH2 = "depth_camera//models//yolo5n-barcode.pt"
ICON_PATH = ""

REDIST_PATH = 'depth_camera//Redist//'
DATA_DIR = 'data'
FOCAL_LENGTH = 70
DEPTH = 200

DEFAULT_FONT = cv2.FONT_HERSHEY_SIMPLEX
DEFAULT_LINE = cv2.LINE_AA
DEFAULT_COLOR = (0, 0, 255)

BLOBS_PARAMS = cv2.SimpleBlobDetector_Params()
BLOBS_PARAMS.minThreshold = 10
BLOBS_PARAMS.maxThreshold = 200
BLOBS_PARAMS.filterByArea = True
BLOBS_PARAMS.minArea = 1500
BLOBS_PARAMS.filterByCircularity = True
BLOBS_PARAMS.minCircularity = 0.1
BLOBS_PARAMS.filterByConvexity = True
BLOBS_PARAMS.minConvexity = 0.87
BLOBS_PARAMS.filterByInertia = True
BLOBS_PARAMS.minInertiaRatio = 0.01
nErosions = 3
maxDepth= 3000
minDepth = 10
edgePixels = 10


def minRatio(a, b):
	if a == 0 or b == 0:
		return 0
	elif a < b:
		return float(a)/float(b)
	else:
		return float(b)/float(a)

def within(val, lo, hi):
	return val >= lo and val <= hi

def contourWithinInertia(ctr, lo, hi):
	rect = cv2.minAreaRect(ctr)
	return within(minRatio(rect[1][0], rect[1][1]), lo, hi)
