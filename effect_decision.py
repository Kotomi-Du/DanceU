import numpy as np
from scipy import signal

class EffectDecision:
    def __init__(self, bbox_info, debug=False):
        self.bbox_info = bbox_info
        self.debug = debug
        self.effect_desc_list = None
        self.effect_point_list = None
        self.default_scale = self.get_default_scale()
        self.default_loc_x, self.default_loc_y = self.get_default_loc()
        self.cfg = {'adjust_loc_x': True,   # try to adjust vertical center of bbox to the view center
                    'adjust_loc_y': True}   # adjust the upper boundary of bbox within view

    def get_default_scale(self):
        default_scale = 1.2  # TODO: to be determined by bbox_info
        return default_scale

    def get_default_loc(self):
        # TODO: to be determined by bbox_info
        default_loc_x = 0.0
        bboxes = self.bbox_info['bboxes']
        h, w = self.bbox_info['frame_size']
        bbox_center_y = (bboxes[:, 1] + bboxes[:, 3]) / 2
        avg_center_y = np.average(bbox_center_y)
        view_center_y = h / 2
        dis_y = (view_center_y - avg_center_y) / h
        loc_y_abs = abs(dis_y) * self.default_scale
        max_loc_y_abs = (self.default_scale - 1) / 2
        loc_y_abs = min(loc_y_abs, max_loc_y_abs)
        default_loc_y = -loc_y_abs if dis_y < 0 else loc_y_abs
        if self.debug is True:
            print('default_loc_y = {}'.format(default_loc_y))
        return default_loc_x, default_loc_y

    def find_steepest(self, data_block, start_frame_idx):
        n = len(data_block)
        steepest = 0
        delta_at_steepest = 0
        idx_of_steepest = 0
        for i in range(1, n):
            delta = data_block[i] - data_block[i-1]
            if abs(delta) > steepest: 
                steepest = abs(delta)
                delta_at_steepest = delta
                idx_of_steepest = i
        
        return (start_frame_idx + idx_of_steepest, delta_at_steepest)

    def find_search_range(self, key_frame_idx, n_frames, frame_rate, length=1, bias=0.1):
        left_st = int(key_frame_idx-(bias*frame_rate)-(length*frame_rate))
        left_ed = int(key_frame_idx-(bias*frame_rate))
        right_st = int(key_frame_idx+(bias*frame_rate))
        right_ed = int(key_frame_idx+(bias*frame_rate)+(length*frame_rate))
        left_range = [left_st, left_ed]
        right_range = [right_st, right_ed]

        if left_range[1] <= 0: left_range = None
        if right_range[0] >= n_frames: right_range = None

        if left_range is not None:
            if left_range[0] < 0 : left_range[0] = 0
        if right_range is not None:
            if right_range[1] >= n_frames: right_range[1] = n_frames - 1

        return (left_range, right_range)

    def find_maxima(self, key_frame, delta, maximas, n_frames, frame_rate=30, srange=1.0):
        res = key_frame
        if delta < 0:
            temp = key_frame-(frame_rate*srange)
            left_bound = int(temp) if temp >= 0 else 0
            for i in range(key_frame, left_bound, -1):
                if i in maximas: 
                    res = i
                    # print('found')
                    break
        else:
            temp = key_frame+(frame_rate*srange)
            right_bound = int(temp) if temp < n_frames else n_frames
            for i in range(key_frame, right_bound, 1):
                if i in maximas: 
                    res = i
                    break

        return res

    def get_effect_list(self, area_data, audio_beats, au_instance, framerate, group_size=4):
        n_frames = len(area_data)
        n_beats = len(audio_beats)
        local_maxima = signal.argrelextrema(area_data, np.greater, axis=0, order=3)
        local_minima = signal.argrelextrema(area_data, np.less, axis=0, order=3)
        minima_dict = dict()
        for item in local_minima[0]:
            minima_dict[item] = 1
        maxima_dict = dict()
        for item in local_maxima[0]:
            maxima_dict[item] = 1
        # a = Audio('resources_video/spring_origin.mp4')
        effect_list = []

        start_list = []
        key_list = []
        end_list = []
        zoom_scale_list = []
        group_list = []

        pre_end_to = -1
        pre_start_from = -1
        pre_key_frame_idx= -1

        for i in range(2, n_beats, group_size):
            if (i + group_size - n_beats)/group_size > 0.5: break
            # if i + group_size >= n_beats: break
            st = audio_beats[i]
            ed = audio_beats[i+group_size] if i+group_size < n_beats else audio_beats[n_beats-1]
            block = area_data[st:ed]

            group_list.append(st)
            group_list.append(ed)

            key_frame_idx, delta = self.find_steepest(block, st)
            key_frame_idx = int(self.find_maxima(key_frame_idx, delta, maxima_dict, n_frames, frame_rate=framerate))
            res = au_instance.get_effect_advice(key_frame_idx, slack_range=10)
            if res['is_audio_beat']: 
                key_frame_idx = res['key_frame']  
            if key_frame_idx == pre_key_frame_idx:
                 continue

            left, right = self.find_search_range(key_frame_idx, n_frames, framerate)
            scale = 1.35
            start_from = None
            end_to = None

            if left is not None and right is not None:
                for j in range(left[1], left[0]-1, -1):
                    if j in minima_dict: 
                        start_from = j
                for j in range(right[0], right[1]+1):
                    if j in minima_dict:
                        end_to = j
            
            if start_from is not None and end_to is not None:
                res = au_instance.get_effect_advice(start_from, slack_range=10)
                if res['is_audio_beat']: 
                    start_from = res['key_frame']             
                res = au_instance.get_effect_advice(end_to, slack_range=10)
                if res['is_audio_beat']: 
                    end_to = res['key_frame']

                real_scale = area_data[key_frame_idx]/ area_data[start_from]
                scale = max(min(real_scale, 1.7), 1.35)

                #make sure start_from is behind the previous effect
                if pre_end_to is not None and start_from != pre_start_from and start_from < pre_end_to:
                    start_from = pre_end_to

                effect_dict={
                'frame':key_frame_idx, 
                'effect':[{'type':'zoom', 'scale':scale}],
                'start_from':start_from,
                'end_to': end_to}

                start_list.append(start_from)
                key_list.append(key_frame_idx)
                end_list.append(end_to)
                zoom_scale_list.append(scale)

                effect_list.append(effect_dict)

            pre_end_to = end_to
            pre_start_from = start_from
            pre_key_frame_idx = key_frame_idx
            if self.debug:
                print("group {}:".format(str(i)),left,right,start_from, key_frame_idx, end_to)
                print(effect_list)
        self.effect_desc_list = effect_list
        if self.debug is True:
            print(self.effect_desc_list)
        return effect_list, start_list, key_list, end_list, zoom_scale_list, group_list

    def make_effect_point_list_from_desc_list(self):
        default_scale = self.default_scale
        default_loc_x = self.default_loc_x
        default_loc_y = self.default_loc_y

        effect_point_list = []
        # Set properties for first two frames
        effect_point_list.extend([
            {'frame': 0, 'scale_x': 1.0, 'scale_y': 1.0, 'location_x': 0.0, 'location_y': 0.0},
            {'frame': 1, 'scale_x': default_scale, 'scale_y': default_scale, 'location_x': default_loc_x,
             'location_y': default_loc_y},
        ])

        # Set properties for start_from, keyframe, and end_to that are described in self.effect_desc_list
        last_key_scale = default_scale
        for effect_desc in self.effect_desc_list:
            # effect_desc={
            # 'frame': key_frame_idx,
            # 'effect': [{'type':'zoom', 'scale':scale}],
            # 'start_from': start_from,
            # 'end_to': end_to}

            # 1. According to effect_desc, get the scale at start_from, keyframe, and end_to.
            key_frame = effect_desc['frame']
            key_scale = last_key_scale
            for effect in effect_desc['effect']:
                if effect['type'] == 'zoom':
                    key_scale = effect['scale'] if effect['scale'] > 1 else default_scale
                    last_key_scale = key_scale
            start_from = effect_desc['start_from']
            start_scale = default_scale
            end_to = effect_desc['end_to']
            end_scale = default_scale

            # 2. According to self.cfg and scale, get the properties of a specific frame_idx,
            #    including frame_idx, scale_x, scale_y, location_x, location_y
            effect_points = self.get_effect_points([{'frame': key_frame, 'scale': key_scale},
                                                    {'frame': start_from, 'scale': start_scale},
                                                    {'frame': end_to, 'scale': end_scale},
                                                    ])
            effect_point_list.extend(effect_points)

        self.effect_point_list = effect_point_list
        if self.debug is True:
            print(self.effect_point_list)
        return effect_point_list

    def get_effect_points(self, frame_scale_list):
        # According to self.cfg, get the full property description of a specific frame_idx
        # including frame_idx, scale_x, scale_y, location_x, location_y
        # If adjust_loc_x/y, calculate loc_x/y based on scale and bbox_info.
        # Otherwise, the loc_x/y will be set to the default value
        effect_points = []
        for frame_scale in frame_scale_list:
            frame_idx = frame_scale['frame']
            if frame_idx is None:
                continue

            scale = frame_scale['scale']

            loc_x = self.default_loc_x
            if 'adjust_loc_x' in self.cfg:
                if self.cfg['adjust_loc_x']:
                    loc_x = self.adjust_loc_x(frame_idx, scale)

            loc_y = self.default_loc_y
            if 'adjust_loc_y' in self.cfg:
                if self.cfg['adjust_loc_y']:
                    loc_y = self.adjust_loc_y(frame_idx, scale)

            effect_points.append({'frame': frame_idx,
                                  'scale_x': scale,
                                  'scale_y': scale,
                                  'location_x': loc_x,
                                  'location_y': loc_y})
        return effect_points

    def adjust_loc_x(self, frame_idx, scale, max_move_limitation=True):
        # try to adjust vertical center of bbox to the view center
        # calculate the distance of bbox to view center
        # right to center: negative
        # left to center: positive
        bbox = self.bbox_info['bboxes'][frame_idx]
        h, w = self.bbox_info['frame_size']
        bbox_center_x = (bbox[0] + bbox[2]) / 2
        view_center_x = w / 2
        dis_x = (view_center_x - bbox_center_x) / w
        loc_x_abs = abs(dis_x)*scale
        # bbox_center_y = (bbox[1] + bbox[3]) / 2
        # view_center_y = h / 2
        # dis_y = (view_center_y - bbox_center_y) / h
        # loc_y_abs = abs(dis_y)*scale

        if max_move_limitation is True:
            max_move = (scale - 1)/2
            loc_x_abs = min(max_move, loc_x_abs)
            # loc_y_abs = min(max_move, loc_y_abs)

        loc_x = -loc_x_abs if dis_x < 0 else loc_x_abs
        # loc_y = -loc_y_abs if dis_x < 0 else loc_y_abs
        return loc_x

    def adjust_loc_y(self, frame_idx, scale):
        # adjust the upper boundary of bbox within view
        bbox = self.bbox_info['bboxes'][frame_idx]
        h, w = self.bbox_info['frame_size']
        half_view_height = h / 2
        bbox_upper_pixel_loc = bbox[1]

        loc_y = self.default_loc_y
        if bbox_upper_pixel_loc < half_view_height:  # there is some bbox in the upper half view
            bbox_upper_height = half_view_height - bbox_upper_pixel_loc
            bbox_upper_height_scaled = bbox_upper_height * scale
            if bbox_upper_height_scaled > half_view_height:  # scaled bbox is out of view
                loc_y = (bbox_upper_height_scaled - half_view_height) / h
        return loc_y

