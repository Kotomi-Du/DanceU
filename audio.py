import librosa
import ffmpeg
import numpy as np
from librosa import onset, beat


class Audio:
    def __init__(self, video_path) -> None:
        self.video_info = ffmpeg.probe(video_path)
        self.framenum = eval(self.video_info['streams'][0]['nb_frames'])
        self.framerate = eval(self.video_info['streams'][0]['r_frame_rate'])
        self.y, self.sr = librosa.load(video_path)

        self.audio_beats = dict()
        self.audio_onsets = []

        self.__analyze_audio()
        self.beats = []
        for k, v in self.audio_beats.items():
            self.beats.append(k)
        

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
            if i in self.audio_beats: 
                return True
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

        onsetenv_timeseq = times[range(0,len(onset_env))]
        onsetenv_frame = self.__times_to_frameidx(onsetenv_timeseq)
        self.onset_length = np.zeros(self.framenum)
        num = np.zeros(self.framenum)
        for i, frame_id in enumerate(onsetenv_frame):
            if frame_id < self.framenum:
                self.onset_length[frame_id] = max(onset_env[i], self.onset_length[frame_id])
                num[frame_id] +=1
        #BPM: beat per minute
        self.tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sr)[0]

    def get_audio_rmse(self):
      '''
      ref: https://musicinformationretrieval.com/energy.html
      '''
      hop_length = 256
      frame_length = 512
      rmse = librosa.feature.rms(self.y, frame_length=frame_length, hop_length=hop_length, center=True)
      rmse = rmse[0]
      frames = range(len(rmse))
      rmse_timeseq = librosa.frames_to_time(frames, sr=self.sr, hop_length=hop_length)
      rmse_vframeseq = self.__times_to_frameidx(rmse_timeseq)
      rmse_in_vframe = np.zeros(self.framenum)
      for i, frame_id in enumerate(rmse_vframeseq):
            if frame_id < self.framenum:
                rmse_in_vframe[frame_id] = max(rmse[i], rmse_in_vframe[frame_id])
      return rmse_in_vframe

if __name__ == '__main__':
    import librosa.display
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(1817/35,5))
    a = Audio('resources_video/spring_origin.mp4')
    ax = figure.add_subplot()
    #librosa.display.waveshow(a.y, a.sr)  #the amplitude envelope of a waveform
    # energy = np.array( [ sum(abs(a.y[i:i+frame_length]**2)) for i in range(0, len(a.y), hop_length) ])
    # energy = energy/ np.linalg.norm(energy) * 10
    #p = librosa.display.specshow(librosa.amplitude_to_db(out, ref=np.max), ax=ax, y_axis='log', x_axis='time')
    figure.savefig('vis_result/spring_wave_2.png')
    