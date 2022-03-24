import numpy as np
from scipy import signal

from audio import Audio

def preprocess_data( data, kernel_size = 10):
    ##rectify some data 361-366
    data[361:367] = data[360]
    #average smooth
    kernel = np.ones(kernel_size) / kernel_size
    temp = np.convolve(data, kernel, mode='same')
    affected_idx = int(kernel_size/2)
    data[affected_idx:-affected_idx] =  temp[affected_idx:-affected_idx] 
    return data

def find_steepest(data_block, start_frame_idx):
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

def find_search_range(key_frame_idx, n_frames, frame_rate, length=1, bias=0.1):
    left_st = int(key_frame_idx-(bias*frame_rate)-(length*frame_rate))
    left_ed = int(key_frame_idx-(bias*frame_rate))
    right_st = int(key_frame_idx+(bias*frame_rate))
    right_ed = int(key_frame_idx+(bias*frame_rate)+(length*frame_rate))
    left_range = [left_st, left_ed]
    right_range = [right_st, right_ed]

    if left_range[1] <= 0: left_range = None
    if right_range[0] >= n_frames: right_range = None

    if left_range[0] < 0 : left_range[0] = 0
    if right_range[1] >= n_frames: right_range[1] = n_frames - 1

    return (left_range, right_range)

def find_maxima(key_frame, delta, maximas, n_frames, frame_rate=30, srange=1.0):
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



def analyze_motion(area_data, audio_beats, group_size=4):
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
    a = Audio('resources_video/spring_origin.mp4')
    effect_list = []
    for i in range(2, n_beats, group_size):
        if (i + group_size - n_beats)/group_size > 0.5: break
        # if i + group_size >= n_beats: break
        st = audio_beats[i]
        ed = audio_beats[i+group_size] if i+group_size < n_beats else audio_beats[n_beats-1]
        block = area_data[st:ed]

        key_frame_idx, delta = find_steepest(block, st)
        key_frame_idx = find_maxima(key_frame_idx, delta, maxima_dict, n_frames)
        left, right = find_search_range(key_frame_idx, n_frames, 30)

        scale = 1.35
        start_from = None
        end_to = None

        if left is not None and right is not None:
            for i in range(left[1], left[0]-1, -1):
                if i in minima_dict: start_from = i
            for i in range(right[0], right[1]+1):
                if i in minima_dict: end_to = i
        
        if start_from is not None and end_to is not None:
            res = a.get_effect_advice(start_from, slack_range=10)
            if res['is_audio_beat']: 
                start_from = res['key_frame']
            res = a.get_effect_advice(key_frame_idx, slack_range=10)
            if res['is_audio_beat']: 
                key_frame_idx = res['key_frame']
            res = a.get_effect_advice(end_to, slack_range=10)
            if res['is_audio_beat']: 
                end_to = res['key_frame']

            real_scale = area_data[key_frame_idx]/ area_data[start_from]
            scale = max(min(real_scale, 1.7), 1.35)

            effect_dict={
            'frame':key_frame_idx, 
            'effect':[{'type':'zoom', 'scale':scale}],
            'start_from':start_from,
            'end_to': end_to}

            start_list.append(start_from)
            key_list.append(key_frame_idx)
            end_list.append(end_to)

            effect_list.append(effect_dict)

    print(effect_list)
    return effect_list

def visualization(area_data):
    import matplotlib.pyplot as plt
    x_data = range(len(area_data))
    # create figure and axis objects with subplots()
    fig,ax = plt.subplots()
    # make a plot
    ax.plot(x_data, area_data, color="green", linestyle='-')
    vis_y = [area_data[i] for i in start_list]
    plt.scatter(start_list, vis_y, color = "black", s = 25)

    vis_y = [area_data[i] for i in key_list]
    plt.scatter(key_list, vis_y, color = "blue", s = 25)

    vis_y = [area_data[i] for i in end_list]
    plt.scatter(end_list, vis_y, color = "black", s = 25)

    #vis_y = [self.area_data[i] for i in  self.delta_x] 
    beats = [16,34,51,69,85,103,121,138,156,174,191,208,226,243,260,278, 296,314,330,348,366,383,401,418,436,454, 471,489,506,523,541,558,576,593, 610]
    vis_y = [area_data[i] for i in beats] 
    plt.scatter( beats, vis_y, color = "red", marker="x", s = 10)
    plt.show()
    plt.savefig("filename.png")

start_list = []
key_list = []
end_list = []


if __name__ == "__main__":
    area_data = np.load( "cache/area_data.npy")
    beats = [16,34,51,69,85,103,121,138,156,174,191,208,226,243,260,278, 296,314,330,348,366,383,401,418,436,454, 471,489,506,523,541,558,576,593, 610]

    area_data = preprocess_data(area_data)
    res = analyze_motion(area_data, beats, group_size=4)
    '''
    x = [i for i in range(1, len(area_data)+1)]
    start_from, key, end_to = [], [], []
    for effect in res:
        start_from.append(effect['start_from'])
        key.append(effect['frame'])
        end_to.append(effect['end_to'])
    from matplotlib import pyplot as plt
    plt.plot(x, area_data)
    for x in start_from:
        plt.axvline(x, ls='-', c='green')
    for x in key:
        plt.axvline(x, ls='-', c='yellow')
    for x in end_to:
        plt.axvline(x, ls='-', c='blue')
    plt.savefig('./plot.jpg')
    '''


    from effect import gen_effects
    gen_effects(res)
    visualization(area_data)
