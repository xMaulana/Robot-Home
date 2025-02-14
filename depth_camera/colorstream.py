from depth_camera.config import *
from depth_camera.utils import _temporal_filter, _add_border, _add_square, _add_polylines

import cv2
import numpy as np
import torch
from ultralytics.utils.plotting import Annotator
from pyzbar import pyzbar
# from inference_sdk import InferenceHTTPClient
device = 'cuda' if torch.cuda.is_available() else 'cpu'

class ColorStream:
    def __init__(self, cam,
                 barcode=True,
                 ):
        
        self.cap = cv2.VideoCapture(cam)
        
        if barcode : 
            self.barcode_auth = 'hahahaha' if barcode else None 
            barcode_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
            barcode_params = cv2.aruco.DetectorParameters()
            self.detector = cv2.aruco.ArucoDetector(barcode_dict, barcode_params)
        
        # try : 
        #     self.CLIENT = InferenceHTTPClient(
        #         api_url="https://detect.roboflow.com",
        #         api_key="1UnUQCCfSuu44HS6CrHe"
        #     )
        
        # except : 
        #     self.CLIENT = None
            
    def get_frame(self, 
                  img_depth=None, 
                  model=None, 
                  gripper_model=None,
                  barcode_model=None,
                  temporal_filter=False,
                  data = None,
                  gripper_loc=None,
                ):
        
        if data :
            self.data = data

        self.temporal_filter = temporal_filter
        if self.temporal_filter:
            self.prev_color_image = None
        
        _, color_image_raw = self.cap.read()

        if color_image_raw is not None:
        
            if data:
                self.data['color']['raw'] = color_image_raw
                
            if self.temporal_filter :
                color_image_raw= _temporal_filter(color_image_raw, self.prev_color_image)
                self.prev_color_image = color_image_raw
            
            if model is not None:
                self.model = model
                color_image = self._yolo(color_image_raw, img_depth)
            
            # if gripper_model is not None:
            #     self.gripper_model = gripper_model
            #     color_image = self._yolo_gripper(color_image, color_image_raw, img_depth)   
            
            if gripper_loc is not None:
                color_image = self._annotate_gripper_segment2(color_image_raw, gripper_loc)
            
            # if self.barcode_auth is not None:
            #     self.barcode_model = barcode_model
            #     color_image = self._annotate_barcode_segment(color_image_raw, color_image_raw, img_depth)
            
            if data : 
                self.data['color']['annot'] = color_image
                return color_image, self.data
            
        else : 
            return None, None
    
    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()
    
    def _yolo(self, img, img_depth=None):
        annotator = Annotator(img)
        results = self.model.predict(img, verbose=False)
        if results:
            for r in results:
                if r.boxes and r.masks: 
                    for box, mask in zip(r.boxes, r.masks):
                        img, annotator = self._annotate_segment(img, box, mask, annotator, img_depth)
                            
        img = annotator.result() 
        return img
    
    def _yolo_gripper(self, img, img_raw, img_depth):
        results = self.gripper_model.predict(img_raw, verbose=False)
        if results:
            for r in results:
                if r.boxes:
                    for box in r.boxes:
                        img = self._annotate_gripper_segment(img, box, img_depth)
        return img
    
    def _annotate_segment(self, img, box, mask, annotator, img_depth) : 
        bbox = box.xyxy[0]
        class_name = self.model.names[int(box.cls)]
        border = mask.xy[0]
        
        annotator.box_label(bbox, class_name)
        img = _add_border(img, border)
        
        mask_segment = mask.data.cpu().numpy()
        mask_segment.shape = (480, 640)

        # img = self._add_distance_estimation(img, mask, img_depth, bbox)
        if img_depth is not None:
            depth_mask = img_depth * mask_segment
            depth_estimation = int(np.sum(depth_mask)/np.sum(mask_segment)/10)
        else :
            mask_segment = None
            depth_estimation = 100

        center = (int(bbox[0] + (bbox[2] - bbox[0])/2), int(bbox[1] + (bbox[3] - bbox[1])/2))
        location = (center[0], center[1], depth_estimation)
        
        img = cv2.putText(img, f'{location}', center, DEFAULT_FONT,  
                0.4, (0, 0, 255), 1, DEFAULT_LINE)
        
        self.data['items_loc'][class_name] = []
        self.data['items_loc'][class_name].append({'bbox':bbox.cpu().numpy(), 
                                                   'location':location, 
                                                   'mask':mask_segment})
        
        return img, annotator
    
    def _annotate_gripper_segment(self, img, box, img_depth=None):
        bbox = box.xyxy[0]
        bbox = [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]
        center = (int(bbox[0] + (bbox[2] - bbox[0])/2), int(bbox[1] + (bbox[3] - bbox[1])/2))
        depth_estimation = 100
        
        location = (center[0], center[1], depth_estimation)
        img = _add_square(img, bbox, center, location, 'GRIPPER')
        self.data['gripper_loc'] = {'bbox':bbox,
                                    'location':location}
        return img
    
    def _annotate_gripper_segment2(self, img, gripper_loc, depth_estimation=0):
        x, y = int(gripper_loc[0]), int(gripper_loc[1])
        size = int(gripper_loc[2])
        x1, y1, x2, y2 = int(x - size), int(y - size), int(x + size), int(y + size)
        self.data['gripper_loc'] = {'bbox':[x1, y1, x2, y2],
                                    'location':(240, 320, depth_estimation)}
     
        img = _add_square(img, (x1, y1, x2, y2), (x, y), (x, y, size), 'GRIPPER') 
        
        return img

    def _annotate_barcode_segment(self, img, img_raw, img_depth):
        location = None
        depth_estimation = 100
        (corners, ids, rejected) = self.detector.detectMarkers(img_raw)
        
        if corners:
            img = _add_polylines(img, corners, 'ARUCO')
            # print(np.array(corners).shape)
            x, y = np.mean(np.array(corners)[0, 0, :, 0]), np.mean(np.array(corners)[0, 0, :, 1])
            location = (x, y, depth_estimation)
        
        self.data['barcode_loc'] = {'corners':corners,
                                    'location':location}
        
        return img