

class Motion:
    def __init__(self, video_path) -> None:
        self.motion2d = self.__get_2dpose()
        self.motion3d = self.__get_2dpose()

        
        '''
        motion_beat
        key: keyframe_index of beat point 
        value： motion_effect_hint  list including: left, right, up, down, forward, backward(need to finetune)
        e.g.  5: [-10, 0 , 0 , 0]
        '''
        self.motion_beats = dict()

        self.__analyze_motion()

    def __get_2dpose(self):
        pass
    
    def __get_3dpose(self):
        pass

    def __analyze_motion(self):
        pass

    def __analyze_pose_direction(self, frame_idx):
        pass
