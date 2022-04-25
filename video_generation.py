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

        self.effect_point_list = None
        self.from_idx = None
        self.to_idx = None

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
                    fancy_effect_list=None,
                    bbox_info=None):
        effect_point_list = self.make_effect_point_list_from_desc(effect_desc_list_new, frame_delta=frame_delta)
        self.edit_video(video_in_path=video_in_path,
                        video_out_path=video_out_path,
                        effect_point_list=effect_point_list,
                        save_from=save_from,
                        save_to=save_to,
                        fancy_effect_list=fancy_effect_list,
                        bbox_info=bbox_info)

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
            # video.location_x.AddPoint(point['frame'], point['location_x'], self.line_type)
            # video.location_y.AddPoint(point['frame'], point['location_y'], self.line_type)

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

        self.effect_point_list = effect_point_list
        return effect_point_list

    def edit_video(self,
                   video_in_path,
                   video_out_path,
                   effect_point_list=None,
                   save_from=None,
                   save_to=None,
                   fancy_effect_list=None,
                   bbox_info=None):
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

        # if bbox_info is not None:
        #     self.adjust_scale(bbox_info)
        self.add_effect_point(clip)
        if bbox_info is not None:
            self.adjust_center(clip, bbox_info, strategy=1, move_type='x', max_move_limitation=True)
            self.adjust_loc_y(clip, bbox_info, strategy=1)

        if fancy_effect_list is not None:
            from effect import get_fancy_effects
            fancy_effects = get_fancy_effects(fancy_effect_list, clip)
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

    def adjust_center(self, video, bbox_info, strategy=1, move_type='xy', max_move_limitation=True):
        # calculate the distance of bbox to view center
        # right to center: negative
        # left to center: positive
        bboxes = bbox_info['bboxes']
        frame_num = bboxes.shape[0]
        h, w = bbox_info['frame_size']
        bbox_center_x = (bboxes[:, 0] + bboxes[:, 2]) / 2
        bbox_center_y = (bboxes[:, 1] + bboxes[:, 3]) / 2

        view_center_x = w / 2
        view_center_y = h / 2
        dis_x = (view_center_x - bbox_center_x) / w
        dis_y = (view_center_y - bbox_center_y) / h

        frame_idx_list = []
        if strategy == 0:
            # adjust locations every 10 frames
            frame_idx_list.extend(list(range(self.from_idx, self.to_idx, 10)))
            frame_idx_list.append(self.to_idx-1)
        elif strategy == 1:
            # on special frames (start_from, keyframe, and end_to)
            for point in self.effect_point_list:
                frame_idx_list.append(point['frame'])
        elif strategy == 2:
            # every 10 frames + special frames
            frame_idx_list.extend(list(range(self.from_idx, self.to_idx, 10)))
            for point in self.effect_point_list:
                frame_idx_list.append(point['frame'])
            frame_idx_list.append(self.to_idx-1)

        for frame_idx in frame_idx_list:
            scale = video.scale_x.GetValue(frame_idx)
            loc_x_abs = abs(dis_x[frame_idx])*scale
            loc_y_abs = abs(dis_y[frame_idx]*scale)

            if max_move_limitation is True:
                max_move = (scale - 1)/2
                loc_x_abs = min(max_move, abs(dis_x[frame_idx])*scale)
                loc_y_abs = min(max_move, abs(dis_y[frame_idx]*scale))

            loc_x = -loc_x_abs if dis_x[frame_idx] < 0 else loc_x_abs
            loc_y = -loc_y_abs if dis_x[frame_idx] < 0 else loc_y_abs
            if move_type == 'x':
                video.location_x.AddPoint(frame_idx, loc_x, self.line_type)
            elif move_type == 'y':
                video.location_y.AddPoint(frame_idx, loc_y, self.line_type)
            elif move_type == 'xy':
                video.location_x.AddPoint(frame_idx, loc_x, self.line_type)
                video.location_y.AddPoint(frame_idx, loc_y, self.line_type)

    def adjust_loc_y(self, video, bbox_info, strategy=1):
        # calculate the distance of bbox to view center
        # right to center: negative
        # left to center: positive
        bboxes = bbox_info['bboxes']
        frame_num = bboxes.shape[0]
        h, w = bbox_info['frame_size']
        half_view_height = h / 2
        bbox_upper_pixel_loc = bboxes[:, 1]

        frame_idx_list = []
        if strategy == 0:
            # adjust locations every 10 frames
            frame_idx_list.extend(list(range(self.from_idx, self.to_idx, 10)))
            frame_idx_list.append(self.to_idx-1)
        elif strategy == 1:
            # on special frames (start_from, keyframe, and end_to)
            for point in self.effect_point_list:
                frame_idx_list.append(point['frame'])
        elif strategy == 2:
            # every 10 frames + special frames
            frame_idx_list.extend(list(range(self.from_idx, self.to_idx, 10)))
            for point in self.effect_point_list:
                frame_idx_list.append(point['frame'])
            frame_idx_list.append(self.to_idx-1)

        for frame_idx in frame_idx_list:
            loc_y = 0.0
            if bbox_upper_pixel_loc[frame_idx] < half_view_height:  # there is some bbox in the upper half view
                scale = video.scale_x.GetValue(frame_idx)
                bbox_upper_height = half_view_height - bbox_upper_pixel_loc[frame_idx]
                bbox_upper_height_scaled = bbox_upper_height * scale
                if bbox_upper_height_scaled > half_view_height:  # scaled bbox is out of view
                    loc_y = (bbox_upper_height_scaled - half_view_height) / h
                    print('debug, frame={}, bbox_upper_height={}, scale={}, loc_y={}'.format(frame_idx, bbox_upper_height, scale, loc_y))
            video.location_y.AddPoint(frame_idx, loc_y, self.line_type)

    def adjust_scale(self, bbox_info, strategy=0):
        bboxes = bbox_info['bboxes']
        h, w = bbox_info['frame_size']
        width = bboxes[:, 2] - bboxes[:, 0]
        height = bboxes[:, 3] - bboxes[:, 1]

        if strategy == 0:
            max_scales_w = w / width
            max_scales_h = h / height

            for point in self.effect_point_list:
                frame_idx = point['frame']
                max_scale = min(max_scales_w[frame_idx], max_scales_h[frame_idx])
                if point['scale_x'] > max_scale:
                    print('adjust_scale: frame={}, scale_before={}, scale_after={}'.format(frame_idx,point['scale_x'], max_scale))
                    point['scale_x'] = max_scale
                    point['scale_y'] = max_scale

        # if strategy == 1:
        #     # make sure bbox not out when loc_x & loc_y keeps 0.0
        #     left = bboxes[:, 0
        #     right = bboxes[:, 2]
        #     up = bboxes[:, 1]
        #     down = bboxes[:, 3]
        #     half_x = w/2
        #     half_h = h/2
        #     max_scale_left = half_x / (half_x - left)
        #     max_scale_right = half_x / (right - half_x)
        #     max_scale_up = half_h / (half_h - up)
        #     max_scale_down = half_h / (down - half_h)
