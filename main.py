from audio import Audio
from motion import Motion

def main():
    video_path = 'resources_video/money_reference.mp4'
    a = Audio(video_path)
    m = Motion(video_path)
    audio_beats = a.audio_beats
    motion_beats = m.motion_beats
 
    for frame_idx, item in audio_beats.items():
            if  m.is_motion_beat(frame_idx):
                previous_frame_idx = -1
                effect_advice = m.get_effect_advice(previous_frame_idx, frame_idx)            
                #do_effect( motion_effect_hint, startframe_index, keyframe_index, endframe_index)
    
    #save_effected_video()


if __name__ == '__main__':
    main()