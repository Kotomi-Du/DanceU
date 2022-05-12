import openshot
import ffmpeg


class VideoGeneration:
    def __init__(self, effect_point_list, fancy_effect_list=None, line_type='linear', debug=False):
        # Bezier curves are quadratic curves, which create a smooth curve.
        # Linear curves are angular, straight lines between two points.
        # Constant curves jump from their previous position to a new one (with no interpolation).
        if line_type == 'linear':
            self.line_type = openshot.LINEAR
        elif line_type == 'bezier':
            self.line_type = openshot.BEZIER
        elif line_type == 'const':
            self.line_type = openshot.CONSTANT
        else:
            self.line_type = openshot.LINEAR

        self.effect_point_list = effect_point_list
        self.fancy_effect_list = fancy_effect_list
        self.from_idx = None
        self.to_idx = None

        self.debug = debug
        self.property_change_curves = {'frame': [],
                                       'scale': [],
                                       'loc_x': [],
                                       'loc_y': [],
                                       'alpha': []}
        pass

    def gen_effects(self,
                    video_in_path="/home/openshot/DanceU/resources_video/spring_origin.mp4",
                    video_out_path="./spring_out.mp4",
                    save_from=0,
                    save_to=None):
        # Create an FFmpegReader
        r = openshot.FFmpegReader(video_in_path)

        r.Open()  # Open the reader
        r.DisplayInfo()  # Display metadata
        video_bit_rate = self.get_bitrate(video_in_path)

        # Set up Writer
        w = openshot.FFmpegWriter(video_out_path)
        w.SetAudioOptions(True,
                          "libmp3lame",  # r.info.acodec,
                          r.info.sample_rate,
                          r.info.channels,
                          r.info.channel_layout,
                          r.info.audio_bit_rate)
        w.SetVideoOptions(True,
                          "libx264",  # r.info.vcodec,
                          openshot.Fraction(r.info.fps.num,
                                            r.info.fps.den),
                          r.info.width,
                          r.info.height,
                          openshot.Fraction(r.info.pixel_ratio.num,
                                            r.info.pixel_ratio.den),
                          r.info.interlaced_frame,
                          r.info.top_field_first,
                          video_bit_rate)

        clip = openshot.Clip(r)
        clip.Open()

        from_idx = 0
        to_idx = r.info.video_length
        if save_from is not None and save_to is not None and save_from < save_to:
            if 0 < save_from < to_idx:
                from_idx = save_from
            if 0 < save_to < to_idx:
                to_idx = save_to
        self.from_idx = from_idx
        self.to_idx = to_idx

        self.add_effect_point(clip)

        if self.fancy_effect_list is not None:
            from effect import get_fancy_effects
            fancy_effects = get_fancy_effects(self.fancy_effect_list, clip)
            for effect in fancy_effects:
                if effect is not None:
                    clip.AddEffect(effect)

        # Open the Writer
        w.Open()

        if self.debug is True:
            self.get_property_change_curves(clip, from_idx, to_idx)

        # Grab frames from Clip and encode to Writer
        for frame in range(from_idx, to_idx):
            # f = r.GetFrame(frame)
            f = clip.GetFrame(frame)
            w.WriteFrame(f)

        # Close out Reader & Writer
        clip.Close()
        w.Close()
        r.Close()
        print("Completed successfully!")

    def get_bitrate(self, file):
        probe = ffmpeg.probe(file)
        video_bitrate = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        bitrate = int(video_bitrate['bit_rate'])
        return bitrate

    def add_effect_point(self, video):
        """This method add effects to a given video.

        Args:
        video: the video to be added effects to.
        effect_desc_dict: a dict that describes the effects.

        # Returns:
        #   video: the video with effects
        """

        for point in self.effect_point_list:
            video.scale_x.AddPoint(point['frame'], point['scale_x'], self.line_type)
            video.scale_y.AddPoint(point['frame'], point['scale_y'], self.line_type)
            video.location_x.AddPoint(point['frame'], point['location_x'], self.line_type)
            video.location_y.AddPoint(point['frame'], point['location_y'], self.line_type)

    def get_property_change_curves(self, video, start, end):
        self.property_change_curves['frame'] = []
        self.property_change_curves['scale'] = []
        self.property_change_curves['loc_x'] = []
        self.property_change_curves['loc_y'] = []
        self.property_change_curves['alpha'] = []
        for idx in range(start, end):
            self.property_change_curves['frame'].append(idx)
            self.property_change_curves['scale'].append(video.scale_x.GetValue(idx))
            self.property_change_curves['loc_x'].append(video.location_x.GetValue(idx))
            self.property_change_curves['loc_y'].append(video.location_y.GetValue(idx))
            self.property_change_curves['alpha'].append(video.alpha.GetValue(idx))
