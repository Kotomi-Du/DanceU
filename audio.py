import librosa
import ffmpeg
import numpy as np
from librosa import onset, beat


class Audio:
    def __init__(self, video_path) -> None:
        self.video_info = ffmpeg.probe(video_path)
        self.framerate = eval(self.video_info['streams'][0]['r_frame_rate'])
        self.y, self.sr = librosa.load(video_path)

        self.audio_beats = dict()
        self.audio_onsets = []

        self.__analyze_audio()
        pass

    def is_audio_beat(self, motion_beat_frame, slack_range=8) -> bool:
        ''' Return whether there is a matched audio beat.
        
        Parameters:
        ----------
        motion_beat_frame : int 
          - Frame index of an detected motion beat.

        slack_range : int
          - A frame range centered on motion_beat_frame in which we search for a matching audio beat.

        Return:
        ----------
        True/False
        '''
        assert isinstance(motion_beat_frame, int), 'Input parameter must be integer'
        for i in range(motion_beat_frame-(slack_range//2), motion_beat_frame+(slack_range//2), 1):
            if i in self.audio_beats: return True
        return False


    def get_effect_advice(self, motion_beat_frame, slack_range=8, farthest_onset=20) -> dict:
        ''' Return effect advice dict.
        
        Parameters:
        ----------
        motion_beat_frame : int 
          - Frame index of an detected motion beat.

        slack_range : int
          - A frame range centered on motion_beat_frame in which we search for a matching audio beat.
        
        farthest_onset : int
          - If we can find an onset within [motion_beat_frame-farthest_onset, motion_beat_frame), 
          it will be determined as the start frame. Otherwise the start frame will be the same as key frame.

        Return:
        ----------
        res : dict
          - {'is_audio_beat':False, 'start_frame':-1, 'key_frame':-1, 'speed':-1}
        '''
        assert isinstance(motion_beat_frame, int), 'Input parameter must be integer'
        assert isinstance(slack_range, int), 'Input parameter must be integer'
        assert isinstance(farthest_onset, int), 'Input parameter must be integer'

        res = {'is_audio_beat':False, 'start_frame':-1, 'key_frame':-1, 'speed':-1}
        for frame_idx in range(motion_beat_frame-(slack_range//2), motion_beat_frame+(slack_range//2), 1):
            if frame_idx in self.audio_beats:
                res['is_audio_beat'] = True
                res['key_frame'] = frame_idx
                res['start_frame'] = frame_idx
                res['speed'] = self.audio_beats[frame_idx]['speed']
                for i in range(frame_idx, frame_idx-farthest_onset, -1):
                    if i in self.audio_onsets:
                        res['start_frame'] = i
        return res
    
    def __times_to_frameidx(self, times):
        times = np.array(times)
        frameidx = (times * self.framerate).astype(int)
        return frameidx
    
    def __speed_classify(self, tempo):
        return 1

    def __analyze_audio(self):
        D = np.abs(librosa.stft(self.y))
        times = librosa.times_like(D, sr = self.sr)
        onset_env = onset.onset_strength(y=self.y, sr=self.sr)
        onsets= onset.onset_detect(onset_envelope=onset_env, sr=self.sr) 
        tempo, beats = beat.beat_track(onset_envelope=onset_env, sr=self.sr)
        beats_timeseq = times[beats]
        onsets_timeseq = times[onsets]
        beats_frame = self.__times_to_frameidx(beats_timeseq)
        self.audio_onsets = self.__times_to_frameidx(onsets_timeseq)

        speed = self.__speed_classify(tempo)

        for idx, frame in enumerate(beats_frame):
            timest = beats_timeseq[idx]
            self.audio_beats[frame] = {'timestamp':timest, 'speed':speed}
  

if __name__ == '__main__':
    a = Audio('resources_video/money_reference.mp4')
    print(a.is_audio_beat(25))
    print(a.get_effect_advice(38))
    