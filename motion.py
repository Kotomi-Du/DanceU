from ov_backend import person_detection
import numpy as np
import pandas as pd

def find_max(ref_idx, data, trend):
    maxvalue = data[ref_idx]
    maxidx = ref_idx
    count = 1
    cur_idx  = int(ref_idx + trend * count)
    while cur_idx > 0 and cur_idx < len(data):
        item = data[cur_idx]
        count += 1
        cur_idx  = int(ref_idx + trend * count)
        if maxvalue < item:
            maxvalue = item
            maxidx = cur_idx
        else:
            break
    return maxidx, maxvalue

def find_min(ref_idx, data, trend):
    trend = trend* (-1)
    minvalue = data[ref_idx]
    minidx = ref_idx
    count = 1
    cur_idx  = int(ref_idx + trend * count)
    while cur_idx > 0 and cur_idx < len(data):
        item = data[cur_idx]
        count += 1
        cur_idx  = int(ref_idx + trend * count)
        if minvalue > item:
            minvalue = item
            minidx = cur_idx
        else:
            break
    return minidx, minvalue

class Motion:
    def __init__(self, video_path) -> None:
        # bboxes is array including elements like [xmin, ymin, xmax, ymax]
        #self.bboxes = person_detection.Infer(video_path)  
        self.area_data = np.load( "cache/area_data.npy")
        self.frame_num = len(self.area_data)
        self.beat_effect = []
        self.related_effect = []
        self.delta_x = []

        
        '''
        motion_beat
        key: keyframe_index of beat point 
        value： motion_effect_hint  list including: left, right, up, down, forward, backward(need to finetune)
        e.g.  5: [-10, 0 , 0 , 0]
        '''
        self.motion_beat_blocks = dict()
        #self.area_data = np.zeros(self.frame_num)

        #self.__analyze_motion()
        #self.active_block_idx = -1

    def __person_detection(self, video_path):
        person_detection.Detect(video_path)
    
    def find_block(self, start_trend, end_trend, ref_block, i, j):
        start_idx = i
        end_idx = j
        new_block = None
        opps_trend = False
        while i < start_trend.shape[0] and  start_trend[i] in ref_block:
            i += 1
            continue
        while j < end_trend.shape[0] and end_trend[j] in ref_block:
            opps_trend = True
            end_idx = j
            j += 1
            continue
        start_trend_right = i if i < start_trend.shape[0] else start_trend.shape[0]-1
        new_block = range(start_trend[start_idx], start_trend[start_trend_right])
        if end_trend[end_idx] > start_trend[start_trend_right] :
            new_block = range(start_trend[start_idx], end_trend[end_idx])      
            
        return i, j, new_block

    def __analyze_motion(self):
        '''
        for i, bbox in enumerate(self.bboxes):
            xmin, ymin, xmax, ymax = bbox;
            area = (xmax-xmin)*(ymax-ymin)
            self.area_data[i] = area  
        '''  
        gradient_up = np.zeros(self.frame_num) 
        gradient_down = np.zeros(self.frame_num) 
        gradient_data = np.zeros(self.frame_num)
        for i in range(self.frame_num):
            if i == 0:
                continue
            gradient = abs(self.area_data[i] - self.area_data[i-1])/self.area_data[i]
            gradient_data[i] = gradient
            if self.area_data[i-1] < self.area_data[i]:
                gradient_up[i]= gradient
            else:
                gradient_down[i]= gradient
                
        huge_up_idx = np.where((gradient_up >0) & (gradient_up > 0))[0]
        huge_down_idx = np.where((gradient_down > 0) & (gradient_down > 0))[0]
        window_scope = 30
        i = 0
        j = 0
        count = 0
        while i < huge_up_idx.shape[0] and j < huge_down_idx.shape[0]:
            if huge_up_idx[i] < huge_down_idx[j]:
                print("convex")
                start_idx = i
                anchor = huge_up_idx[start_idx]
                block = range(anchor, anchor+window_scope)
                i, j, block = self.find_block(huge_up_idx, huge_down_idx, block, i, j)
                if block is not None:
                    min_area = np.min(self.area_data[block])
                    max_area = np.max(self.area_data[block])
                    self.motion_beat_blocks[count] = {"trend": "scale_up", "block": block, "min_value": min_area, "max_value": max_area}
            else:
                print("concave")
                start_idx = j
                anchor = huge_down_idx[start_idx]
                block = range(anchor, anchor+window_scope)
                j, i, block = self.find_block(huge_down_idx, huge_up_idx, block, j , i)
                if block is not None:
                    min_area = np.min(self.area_data[block])
                    max_area = np.max(self.area_data[block])
                    self.motion_beat_blocks[count] = {"trend": "scale_down", "block": block, "min_value": min_area, "max_value": max_area}
            count += 1
        print("end")

    def is_motion_beat(self, frame_idx):
        self.active_block_idx = -1
        for k, v in self.motion_beat_blocks.items():
            block = v["block"]
            if frame_idx in block:  # 增加模糊查询
                self.active_block_idx = k
                return True

        return False
    
    def get_effect_advice(self, pre_idx, cur_idx):
        scale = self.area_data[cur_idx] / self.area_data[pre_idx]
        '''
        #another method
        if self.active_block_idx != -1:
            block_info = self.motion_beat_blocks[self.active_block_idx]
            if block_info["trend"] == "scale_down":
                scale = block_info["min_value"] / block_info["max_value"]
            else:
                scale = block_info["max_value"] / block_info["min_value"]
        '''
        desc_dic = {}
        desc_dic['frame'] = cur_idx
        desc_dic['effect'].append({'type': 'zoom', 'scale': scale})
        desc_dic['start_from'] = pre_idx
        desc_dic['end_to'] = None
        return desc_dic

    def __analyze_pose_direction(self, frame_idx):
        pass
    

    def visual_motion_beats(self):
        import matplotlib.pyplot as plt
        fig,ax = plt.subplots()
        for k, v in self.motion_beat_blocks.items():
            start_idx = v["block"][0]
            end_idx = v["block"][-1]
            if v["trend"] == "scale_up":
                ax.plot(v["block"], self.area_data[v["block"]], color="green", linestyle='-')    
                ax.vlines([start_idx, end_idx], v["min_value"],v["max_value"], linestyles = "dashed", colors = "red")
            if v["trend"] == "scale_down":
                ax.plot(v["block"], self.area_data[v["block"]], color="orange", linestyle='-')
                ax.vlines([start_idx, end_idx], v["min_value"],v["max_value"], linestyles = "dashed", colors = "red")
        audio_beat = [16,34,51,69,85,103,121,138,156,174,191,208,226,243,260,278, 296,314,330,348,366,383,401,418,436,454, 471,489,506,523,541,558,576,593, 610]
        vis_audio_x = []
        vis_audio_y = []
        for frame_idx in audio_beat:
            if self.is_motion_beat(frame_idx):
                vis_audio_x.append(frame_idx)
                vis_audio_y.append( self.area_data[frame_idx])
        plt.scatter(vis_audio_x, vis_audio_y, color = "black", s = 25)
        plt.show()
    
    def preprocess_data(self):
        ##rectify some data 361-366
        self.area_data[361:367] = self.area_data[360]
        #average smooth
        kernel_size = 10
        kernel = np.ones(kernel_size) / kernel_size
        self.area_data = np.convolve(self.area_data, kernel, mode='same')
    

    def analyze_motion(self, audio_beats):
        delta_rate = np.zeros(self.frame_num)
        delta_trend = np.zeros(self.frame_num)
        for i in range(self.frame_num):
            if i == 0:
                continue
            delta_rate[i]= abs(self.area_data[i-1]-self.area_data[i] )/self.area_data[i]
            if self.area_data[i-1] > self.area_data[i]:
                delta_trend[i] = -1
            else:
                delta_trend[i] = 1
        first_beat_idx = 2
        group_len = 4
        count = 0
        loop = (len(audio_beats) - first_beat_idx)/group_len
        while count < loop :
            group_beat = audio_beats[first_beat_idx + count*group_len: first_beat_idx + (count+1)*group_len]
            count += 1
            if len(group_beat) != group_len:
                continue
            start_idx = group_beat[0]
            end_idx = group_beat[-1]
            max_area_idx = np.argmax(self.area_data[start_idx: end_idx]) + start_idx
            min_area_idx = np.argmin(self.area_data[start_idx: end_idx]) + start_idx
            max_delta_idx = np.argmax(delta_rate[start_idx: end_idx]) + start_idx

            data = []
            for item in group_beat:
                dic = {}
                dic["beat"] = item
                dic["dis_maxdelta"] = abs(item-max_delta_idx)
                dic["dic_minarea"] = abs(item-min_area_idx)
                dic["dic_maxarea"] = abs(item-max_area_idx)
                dic["idx_maxdelta"] = max_delta_idx
                data.append(dic)
            df = pd.DataFrame(data)
            df1 = df.sort_values(by=['dis_maxdelta', 'dic_minarea', 'dic_maxarea'])
            effectbeat_idx = df1["beat"].head(1).tolist()[0]
            maxdelta_idx = df1["idx_maxdelta"].head(1).tolist()[0]
            if (delta_trend[maxdelta_idx]  == -1 and maxdelta_idx < effectbeat_idx)\
                or (delta_trend[maxdelta_idx]  == 1 and maxdelta_idx > effectbeat_idx):
                related_idx, value = find_max(effectbeat_idx, self.area_data, delta_trend[maxdelta_idx])

            else:
                related_idx, value = find_min(effectbeat_idx, self.area_data, delta_trend[maxdelta_idx])

            self.beat_effect.append(effectbeat_idx)
            self.delta_x.append(maxdelta_idx)
            self.related_effect.append(related_idx)
    
    def visualization(self):
        import matplotlib.pyplot as plt
        x_data = range(len(self.area_data))
        # create figure and axis objects with subplots()
        fig,ax = plt.subplots()
        # make a plot
        ax.plot(x_data, self.area_data, color="green", linestyle='-')
        vis_y = [self.area_data[i] for i in self.beat_effect]
        plt.scatter(self.beat_effect, vis_y, color = "black", s = 25)

        vis_y = [self.area_data[i] for i in self.related_effect]
        plt.scatter(self.related_effect, vis_y, color = "blue", s = 25)

        vis_y = [self.area_data[i] for i in  self.delta_x] 
        plt.scatter( self.delta_x, vis_y, color = "red", s = 10)
        plt.show()


    def get_effect_desc(self):
        result_list = []
        for effectbeat_idx, related_idx in zip(self.beat_effect, self.related_effect):
            desc_dic = {}
            desc_dic['effect'] = []
            scale = self.area_data[effectbeat_idx]/self.area_data[related_idx] - 1
            desc_dic['effect'].append({'type': 'zoom', 'scale': abs(scale)})
            if scale > 0:
                desc_dic['frame'] = effectbeat_idx
                if effectbeat_idx < related_idx:
                    desc_dic['end_to'] = related_idx
                    desc_dic['start_from'] = None
                
                else:
                    desc_dic['start_from'] = related_idx
                    desc_dic['end_to']  = None
            else:
                desc_dic['frame'] = related_idx
                if related_idx < effectbeat_idx:
                    desc_dic['end_to'] = effectbeat_idx
                    desc_dic['start_from'] = None
                
                else:
                    desc_dic['start_from'] = effectbeat_idx
                    desc_dic['end_to']  = None

            result_list.append(desc_dic)
        return result_list




if __name__ == '__main__':
    m = Motion("resources_video\spring_origin.mp4")
    beats = [16,34,51,69,85,103,121,138,156,174,191,208,226,243,260,278, 296,314,330,348,366,383,401,418,436,454, 471,489,506,523,541,558,576,593, 610]
    m.preprocess_data()
    m.analyze_motion(beats)
    m.visualization()
    print(m.get_effect_desc())
