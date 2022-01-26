from audio import Audio
from motion import Motion

def main():
    video_path = 'resources_video/money_reference.mp4'
    a = Audio(video_path)
    m = Motion(video_path)
    audio_beats = a.audio_beats
    motion_beats = m.motion_beats

    for keyframe_index, motion_effect_hint in motion_beats.items():
            if  a.is_audio_beat(keyframe_index):
                effect_advice = a.get_effect_advice(keyframe_index) 
                endframe_index  = effect_advice["endframe_index"]
                startframe_index = effect_advice["startframe_index"]            
                do_effect( motion_effect_hint, startframe_index, keyframe_index, endframe_index)
    
    save_effected_video()


if __name__ == '__main__':
    main()