import numpy as np
import os

from person_detection import Infer
from audio import Audio
from motion2 import preprocess_data, analyze_motion
from effect import gen_effects
from visualization import draw_shapes_to_special_images, visualization


def main(video_path, output_dir, debug):
    # analyze motion
    bounding_boxes = Infer(video_path, debug=debug)
    area_data = calc_area(bounding_boxes)
    area_data = preprocess_data(area_data)

    # analyze audio
    a = Audio(video_path)
    audio_beats = a.audio_beats
    framerate = a.framerate
    beats = []
    for k, v in audio_beats.items():
        beats.append(k)

    # get effects based on music and motion
    res, start_list, key_list, end_list, zoom_scale_list, group_list = analyze_motion(area_data, beats, a, framerate, group_size=4)

    # generate edited video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(output_dir, '{}_out.mp4'.format(video_name))
    gen_effects(res, video_in_path=video_path, video_out_path=out_path)

    if debug is True:
        visualization(area_data, start_list, key_list, end_list, video_name, beats, group_list, zoom_scale_list)
        infer_debug_folder = os.path.join('detection_result', video_name)  # ToDo: use Infer.debug_folder
        draw_shapes_to_special_images(infer_debug_folder, start_list, key_list, end_list, beats)


def calc_area(bboxes):
    area_data = []
    for bbox in bboxes:
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        area_data.append(area)
    area_data = np.array(area_data)
    return area_data


if __name__ == '__main__':
    # ToDo: Use arg parser
    video_path = 'resources_video/spring_origin.mp4'
    output_dir = 'output'
    debug = True

    if not os.path.exists(video_path):
        print('{} does not exit!'.format(video_path))

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    main(video_path, output_dir, debug)
