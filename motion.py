import numpy as np
from person_detection import Infer
class Motion:
    def __init__(self, video_path, debug):
        self.video_path = video_path
        bounding_boxes = Infer(video_path, debug=debug)
        t_area_data = self.calc_area(bounding_boxes)
        self.area_data = self.preprocess_data(t_area_data)

    def preprocess_data(self, data, kernel_size = 10):
        ##rectify some data 361-366
        # data[361:367] = data[360]
        #average smooth
        kernel = np.ones(kernel_size) / kernel_size
        temp = np.convolve(data, kernel, mode='same')
        affected_idx = int(kernel_size/2)
        data[affected_idx:-affected_idx] =  temp[affected_idx:-affected_idx] 

        return data
    
    def calc_area(self, bboxes):
        area_data = []
        for bbox in bboxes:
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            area_data.append(area)
        area_data = np.array(area_data)

        return area_data