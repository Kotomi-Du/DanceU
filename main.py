import os
import argparse

from audio import Audio
from visualization import draw_shapes_to_special_images, draw_decision_statistics, draw_audio_feature, draw_video_property_curve
from motion import Motion
from effect_decision import EffectDecision
from video_generation import VideoGeneration

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
    res, start_list, key_list, end_list, zoom_scale_list, group_list = eff.get_effect_list(area_data, beats, ado, framerate, group_size=2)

    # generate edited video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(output_dir, '{}_out.mp4'.format(video_name))
    enc = VideoGeneration(line_type='linear', debug=debug)
    enc.gen_effects(res, video_in_path=video_path, video_out_path=out_path)

    if debug is True:
        draw_audio_feature(ado.onset_length, ado.get_audio_rmse(), ado.tempo, beats,  video_name)
        draw_video_property_curve(enc.property_change_curves, prop_type='scale', title=video_name)
        draw_decision_statistics(area_data, start_list, key_list, end_list, video_name, beats, group_list, zoom_scale_list)
        infer_debug_folder = os.path.join('detection_result', video_name)  # ToDo: use Infer.debug_folder
        draw_shapes_to_special_images(infer_debug_folder, start_list, key_list, end_list, beats)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-path', type=str, default='resources_video/spring_origin.mp4', help='video path')
    parser.add_argument('--output-dir', type=str, default='output', help='output dir')
    parser.add_argument('--debug', help="Optional. Don't show output.", action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    if not os.path.exists(args.video_path):
        print('{} does not exist!'.format(args.video_path))
    else:
        if os.path.isdir(args.video_path):
            for filename in os.listdir(args.video_path):
                video_path = os.path.join(args.video_path, filename)
                main(video_path, args.output_dir, args.debug)
        else:
            main(args.video_path, args.output_dir, args.debug)
