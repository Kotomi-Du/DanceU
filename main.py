import numpy as np

from audio import Audio
from motion2 import preprocess_data, analyze_motion
from effect import gen_effects

def main(video_path, area_data):
    a = Audio(video_path)
    audio_beats = a.audio_beats
    beats = []
    for k, v in audio_beats.items(): beats.append(k)
    area_data = preprocess_data(area_data)
    res = analyze_motion(area_data, beats, a, group_size=4)
    gen_effects(res)


if __name__ == '__main__':
    video_path = 'resources_video/spring_origin.mp4'
    area_data = np.load( "cache/area_data.npy")

    main(video_path, area_data)