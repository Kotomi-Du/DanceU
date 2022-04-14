import openshot
import ffmpeg

class VideoEncoding:
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
        effect_point_list = self.make_effect_point_list_from_desc_new(effect_desc_list_new, frame_delta=frame_delta)
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


    def add_effect(self, video, effect_desc_list):
        """This method add effects to a given video.

        Args:
        video: the video to be added effects to.
        effect_desc_list: a dict that describes the effects. {'type': 'zoom}

        # Returns:
        #   video: the video with effects
        """
        for effect in effect_desc_list:
            if effect['type'] == 'zoom':
                video.scale_x.AddPoint(effect['frame'][0], effect['scale_x'][0], self.line_type)
                video.scale_x.AddPoint(effect['frame'][1], effect['scale_x'][1], self.line_type)
                video.scale_y.AddPoint(effect['frame'][0], effect['scale_y'][0], self.line_type)
                video.scale_y.AddPoint(effect['frame'][1], effect['scale_y'][1], self.line_type)
                video.location_x.AddPoint(effect['frame'][0], effect['location_x'][0], self.line_type)
                video.location_x.AddPoint(effect['frame'][1], effect['location_x'][1], self.line_type)
                video.location_y.AddPoint(effect['frame'][0], effect['location_y'][0], self.line_type)
                video.location_y.AddPoint(effect['frame'][1], effect['location_y'][1], self.line_type)
            else:
                print('Only zoom effect is supported for now!')


    def add_effect_dict(self, video, effect_desc_dict):
        """This method add effects to a given video.

        Args:
        video: the video to be added effects to.
        effect_desc_dict: a dict that describes the effects.

        # Returns:
        #   video: the video with effects
        """

        point_num = len(effect_desc_dict['frame'])
        for i in range(point_num):
            video.scale_x.AddPoint(effect_desc_dict['frame'][i], effect_desc_dict['scale_x'][i], self.line_type)
            video.scale_y.AddPoint(effect_desc_dict['frame'][i], effect_desc_dict['scale_y'][i], self.line_type)
            video.location_x.AddPoint(effect_desc_dict['frame'][i], effect_desc_dict['location_x'][i], self.line_type)
            video.location_y.AddPoint(effect_desc_dict['frame'][i], effect_desc_dict['location_y'][i], self.line_type)


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

    def make_effect_point_list_from_desc_new(self, effect_desc_list, default_scale=1.2, scale_delta=0.1, frame_delta=5):
        effect_point_list = []
        default_loc_x = 0.0
        default_loc_y = -(default_scale-1.0)/2
        effect_point_list.extend([
            {'frame': 0, 'scale_x': 1.0, 'scale_y': 1.0, 'location_x': 0.0, 'location_y': 0.0},
            {'frame': 1, 'scale_x': default_scale, 'scale_y': default_scale, 'location_x': default_loc_x, 'location_y': default_loc_y},
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

                # frame1 = effect_desc['start_from'] if effect_desc['start_from'] is not None else key_frame - frame_delta
                # frame2 = key_frame
                # frame3 = effect_desc['end_to'] if effect_desc['end_to'] is not None else key_frame + frame_delta

                # effect_point_list.extend([
                #     {'frame': frame1, 'scale_x': default_scale, 'scale_y': default_scale, 'location_x': default_loc_x, 'location_y': default_loc_y},
                #     {'frame': frame2, 'scale_x': key_scale, 'scale_y': key_scale, 'location_x': key_loc_x, 'location_y': key_loc_y},
                #     {'frame': frame3, 'scale_x': default_scale, 'scale_y': default_scale, 'location_x': default_loc_x, 'location_y': default_loc_y},
                # ])

        return effect_point_list


    def add_fancy_effects(self, video, fancy_effect_list):
        for effect in fancy_effect_list:
            if effect['effect'] == 'screen_pump':
                key_frame = effect['frame']
                start_frame = key_frame - effect['offset']
                end_frame = key_frame + effect['offset']
                key_scale = video.scale_x.GetValue(key_frame) * effect['scale']
                start_scale = video.scale_x.GetValue(start_frame)
                end_scale = video.scale_x.GetValue(end_frame)
                video.scale_x.AddPoint(key_frame, key_scale, self.line_type)
                video.scale_y.AddPoint(key_frame, key_scale, self.line_type)
                video.scale_x.AddPoint(start_frame, start_scale, self.line_type)
                video.scale_y.AddPoint(start_frame, start_scale, self.line_type)
                video.scale_x.AddPoint(end_frame, end_scale, self.line_type)
                video.scale_y.AddPoint(end_frame, end_scale, self.line_type)
            if effect['effect'] == 'strobe':
                pass  #TODO: fix the issue of "fail to call video.GetFrame() outside this func"
                # brightness_curve = openshot.Keyframe()
                # brightness_value = 0.0
                # for idx in range(effect['start_from'], effect['end_to'], effect['interval']):
                #     brightness_curve.AddPoint(idx, brightness_value, openshot.CONSTANT)
                #     brightness_value = -1.0 - brightness_value
                # brightness_curve.AddPoint(effect['end_to'], 0.0, openshot.CONSTANT)
                #
                # contrast_curve = openshot.Keyframe()
                # contrast_curve.AddPoint(1, 0.0, openshot.CONSTANT)
                # contrast_curve.AddPoint(effect['end_to'], 0.0, openshot.CONSTANT)
                #
                # brightness_effect = openshot.Brightness(brightness_curve, contrast_curve)
                # video.AddEffect(brightness_effect)


    def edit_video(self,
                   video_in_path,
                   video_out_path,
                   effect_desc_list=None,
                   effect_desc_dict=None,
                   effect_point_list=None,
                   save_from=None,
                   save_to=None,
                   fancy_effect_list=None):
        # Create an FFmpegReader
        r = openshot.FFmpegReader(video_in_path)

        r.Open()         # Open the reader
        r.DisplayInfo()  # Display metadata
        video_bit_rate = self.get_bitrate(video_in_path)

        # Set up Writer
        w = openshot.FFmpegWriter(video_out_path)

        # w.SetAudioOptions(True, "libmp3lame", r.info.sample_rate, r.info.channels, r.info.channel_layout, 128000)
        # w.SetVideoOptions(True, "libx264", openshot.Fraction(30000, 1000), 1920, 1080,
        #                   openshot.Fraction(1, 1), False, False, 3000000)

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

        if effect_desc_list is not None:
            self.add_effect(clip, effect_desc_list)

        if effect_desc_dict is not None:
            self.add_effect_dict(clip, effect_desc_dict)

        if effect_point_list is not None:
            self.add_effect_point(clip, effect_point_list)

        if fancy_effect_list is not None:
            # self.add_fancy_effects(clip, fancy_effect_list)
            for effect in fancy_effect_list:
                if effect['effect'] == 'screen_pump':
                    key_frame = effect['frame']
                    start_frame = key_frame - effect['offset']
                    end_frame = key_frame + effect['offset']
                    key_scale = clip.scale_x.GetValue(key_frame) * effect['scale']
                    start_scale = clip.scale_x.GetValue(start_frame)
                    end_scale = clip.scale_x.GetValue(end_frame)
                    clip.scale_x.AddPoint(key_frame, key_scale, self.line_type)
                    clip.scale_y.AddPoint(key_frame, key_scale, self.line_type)
                    clip.scale_x.AddPoint(start_frame, start_scale, self.line_type)
                    clip.scale_y.AddPoint(start_frame, start_scale, self.line_type)
                    clip.scale_x.AddPoint(end_frame, end_scale, self.line_type)
                    clip.scale_y.AddPoint(end_frame, end_scale, self.line_type)

                if effect['effect'] == 'strobe':
                    brightness_curve = openshot.Keyframe()
                    brightness_value = 0.0
                    for idx in range(effect['start_from'], effect['end_to'], effect['interval']):
                        brightness_curve.AddPoint(idx, brightness_value, openshot.CONSTANT)
                        brightness_value = -1.0 - brightness_value
                    brightness_curve.AddPoint(effect['end_to'], 0.0, openshot.CONSTANT)

                    contrast_curve = openshot.Keyframe()
                    contrast_curve.AddPoint(1, 0.0, openshot.CONSTANT)
                    contrast_curve.AddPoint(effect['end_to'], 0.0, openshot.CONSTANT)

                    brightness_effect = openshot.Brightness(brightness_curve, contrast_curve)
                    clip.AddEffect(brightness_effect)

        # Open the Writer
        w.Open()

        from_idx=0
        to_idx=r.info.video_length
        if save_from is not None and save_to is not None:
            from_idx=save_from
            to_idx=save_to

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

