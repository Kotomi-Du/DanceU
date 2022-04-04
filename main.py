import numpy as np
import os

from person_detection import Infer
from audio import Audio
from motion2 import preprocess_data, analyze_motion, visualization
from effect import gen_effects

def main(video_path, area_data):
    a = Audio(video_path)
    video_title = os.path.splitext(os.path.basename(video_path))[0]
    audio_beats = a.audio_beats
    framerate = a.framerate
    beats = []
    for k, v in audio_beats.items(): beats.append(k)
    area_data = preprocess_data(area_data)
    res, start_list, key_list, end_list, zoom_scale_list, group_list = analyze_motion(area_data, beats, a, framerate, group_size=4)
    out_path = './output/{}_out.mp4'.format(video_title)
    gen_effects(res,video_in_path=video_path, video_out_path=out_path)
    visualization(area_data, start_list, key_list, end_list, video_title, beats, group_list, zoom_scale_list)

def calc_area(video_path):
    bboxes = Infer(video_path)
    area_data = []
    for bbox in bboxes:
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        area_data.append(area)

    return area_data

if __name__ == '__main__':
    video_path = 'resources_video/YiyanWannian_origin.mp4'

    area_data = np.array(calc_area(video_path))
    # area_data = np.load( "cache/area_data.npy")

    main(video_path, area_data)