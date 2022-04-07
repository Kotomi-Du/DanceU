import os
import argparse

from audio import Audio
from visualization import draw_shapes_to_special_images, visualization
from motion import Motion
from effect_decision import EffectDecision
from video_encoding import VideoEncoding

def main(video_path, output_dir, debug):
    # analyze motion
    m = Motion(video_path=video_path, debug=debug)
    area_data = m.area_data

    # analyze audio
    ado = Audio(video_path)
    framerate = ado.framerate
    beats = ado.beats

    # get effects based on music and motion
    eff = EffectDecision(debug=debug)
    res, start_list, key_list, end_list, zoom_scale_list, group_list = eff.get_effect_list(area_data, beats, ado, framerate, group_size=4)

    # generate edited video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(output_dir, '{}_out.mp4'.format(video_name))
    enc = VideoEncoding()
    enc.gen_effects(res, video_in_path=video_path, video_out_path=out_path)

    if debug is True:
        visualization(area_data, start_list, key_list, end_list, video_name, beats, group_list, zoom_scale_list)
        infer_debug_folder = os.path.join('detection_result', video_name)  # ToDo: use Infer.debug_folder
        draw_shapes_to_special_images(infer_debug_folder, start_list, key_list, end_list, beats)


if __name__ == '__main__':
    # ToDo: Use arg parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-path', type=str, default='resources_video/spring_origin.mp4', help='video path')
    parser.add_argument('--output-dir', type=str, default='output', help='output dir')
    parser.add_argument('--debug', default=False, help='debug')
    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print('{} does not exit!'.format(args.video_path))

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    main(args.video_path, args.output_dir, args.debug)
