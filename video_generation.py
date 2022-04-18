import openshot
import ffmpeg


class VideoGeneration:
    def __init__(self, line_type='linear', debug=False):
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

        self.debug = debug
        self.property_change_curves = {'frame': [],
                                       'scale': [],
                                       'loc_x': [],
                                       'loc_y': [],
                                       'alpha': []}
        pass

    def gen_effects(self, effect_desc_list_new,
                    video_in_path="/home/openshot/DanceU/resources_video/spring_origin.mp4",
                    video_out_path="./spring_out.mp4",
                    frame_delta=10,
                    save_from=0,
                    save_to=None,
                    fancy_effect_list=None):
        effect_point_list = self.make_effect_point_list_from_desc(effect_desc_list_new, frame_delta=frame_delta)
        self.edit_video(video_in_path=video_in_path,
                        video_out_path=video_out_path,
                        effect_point_list=effect_point_list,
                        save_from=save_from,
                        save_to=save_to,
                        fancy_effect_list=fancy_effect_list)

    def get_bitrate(self, file):
        probe = ffmpeg.probe(file)
        video_bitrate = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        bitrate = int(video_bitrate['bit_rate'])
        return bitrate

    def add_effect_point(self, video, effec_point_list):
        """This method add effects to a given video.

        Args:
        video: the video to be added effects to.
        effect_desc_dict: a dict that describes the effects.

        # Returns:
        #   video: the video with effects
        """

        for point in effec_point_list:
            video.scale_x.AddPoint(point['frame'], point['scale_x'], self.line_type)
            video.scale_y.AddPoint(point['frame'], point['scale_y'], self.line_type)
            video.location_x.AddPoint(point['frame'], point['location_x'], self.line_type)
            video.location_y.AddPoint(point['frame'], point['location_y'], self.line_type)

    def make_effect_point_list_from_desc(self, effect_desc_list, default_scale=1.2, scale_delta=0.1, frame_delta=5):
        effect_point_list = []
        default_loc_x = 0.0
        default_loc_y = -(default_scale - 1.0) / 2
        effect_point_list.extend([
            {'frame': 0, 'scale_x': 1.0, 'scale_y': 1.0, 'location_x': 0.0, 'location_y': 0.0},
            {'frame': 1, 'scale_x': default_scale, 'scale_y': default_scale, 'location_x': default_loc_x,
             'location_y': default_loc_y},
        ])
        scale = default_scale
        for effect_desc in effect_desc_list:
            key_frame = effect_desc['frame']
            key_scale = scale
            key_loc_x = default_loc_x
            key_loc_y = default_loc_y
            for effect in effect_desc['effect']:
                if effect['type'] == 'zoom':
                    # key_scale = default_scale + effect['scale'] if default_scale + effect['scale'] > 1 else default_scale
                    key_scale = effect['scale'] if effect['scale'] > 1 else default_scale
                    scale = key_scale
                if effect['type'] == 'move':
                    key_scale = scale
                    key_loc_x = effect['location_x']

                effect_points = []
                if effect_desc['start_from'] is not None:
                    effect_points.append({'frame': effect_desc['start_from'],
                                          'scale_x': default_scale,
                                          'scale_y': default_scale,
                                          'location_x': default_loc_x,
                                          'location_y': default_loc_y})
                effect_points.append({'frame': key_frame,
                                      'scale_x': key_scale,
                                      'scale_y': key_scale,
                                      'location_x': key_loc_x,
                                      'location_y': key_loc_y})
                if effect_desc['end_to'] is not None:
                    effect_points.append({'frame': effect_desc['end_to'],
                                          'scale_x': default_scale,
                                          'scale_y': default_scale,
                                          'location_x': default_loc_x,
                                          'location_y': default_loc_y})
                effect_point_list.extend(effect_points)

        return effect_point_list

    def edit_video(self,
                   video_in_path,
                   video_out_path,
                   effect_point_list=None,
                   save_from=None,
                   save_to=None,
                   fancy_effect_list=None):
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

        if effect_point_list is not None:
            self.add_effect_point(clip, effect_point_list)

        if fancy_effect_list is not None:
            from effect import get_fancy_effects
            fancy_effects = get_fancy_effects(fancy_effect_list, clip)
            for effect in fancy_effects:
                if effect is not None:
                    clip.AddEffect(effect)

        # Open the Writer
        w.Open()

        from_idx = 0
        to_idx = r.info.video_length
        if save_from is not None and save_to is not None and save_from < save_to:
            if 0 < save_from < to_idx:
                from_idx = save_from
            if 0 < save_to < to_idx:
                to_idx = save_to

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
