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

    def is_audio_beat(self, motion_beat_frame):
        assert isinstance(motion_beat_frame, int), 'Input parameter must be integer'
        for i in range(motion_beat_frame-5, motion_beat_frame+5, 1):
            if i in self.audio_beats: return True
        return False


    def get_effect_advice(self, motion_beat_frame):
        assert isinstance(motion_beat_frame, int), 'Input parameter must be integer'
        res = {'is_audio_beat':False, 'start_frame':-1, 'key_frame':-1}
        for frame_idx in range(motion_beat_frame-5, motion_beat_frame+5, 1):
            if frame_idx in self.audio_beats:
                res['is_audio_beat'] = True
                res['key_frame'] = frame_idx
                res['start_frame'] = frame_idx
                for i in range(frame_idx, frame_idx-30, -1):
                    if i in self.audio_onsets:
                        res['start_frame'] = i
        return res
    
    def __times_to_frameidx(self, times):
        times = np.array(times)
        frameidx = (times * self.framerate).astype(np.int)
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
    