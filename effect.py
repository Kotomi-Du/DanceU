import openshot


def apply_screen_pump_effect(video, effect_desc, line_type=openshot.LINEAR):
    # screen_pump_effect = {'effect': 'screen_pump', 'frame': 92, 'scale': 1.3, 'offset': 2}
    key_frame = effect_desc['frame']
    start_frame = key_frame - effect_desc['offset']
    end_frame = key_frame + effect_desc['offset']
    key_scale = video.scale_x.GetValue(key_frame) * effect_desc['scale']
    start_scale = video.scale_x.GetValue(start_frame)
    end_scale = video.scale_x.GetValue(end_frame)
    video.scale_x.AddPoint(key_frame, key_scale, line_type)
    video.scale_y.AddPoint(key_frame, key_scale, line_type)
    video.scale_x.AddPoint(start_frame, start_scale, line_type)
    video.scale_y.AddPoint(start_frame, start_scale, line_type)
    video.scale_x.AddPoint(end_frame, end_scale, line_type)
    video.scale_y.AddPoint(end_frame, end_scale, line_type)


def get_strobe_effect(effect_desc):
    # strobe_effect = {'effect': 'strobe', 'start_from': 168, 'end_to': 176, 'interval': 1}
    brightness_curve = openshot.Keyframe()
    brightness_value = 0.0
    for idx in range(effect_desc['start_from'], effect_desc['end_to'], effect_desc['interval']):
        brightness_curve.AddPoint(idx, brightness_value, openshot.CONSTANT)
        brightness_value = -1.0 - brightness_value
    brightness_curve.AddPoint(effect_desc['end_to'], 0.0, openshot.CONSTANT)
    
    contrast_curve = openshot.Keyframe()
    contrast_curve.AddPoint(1, 0.0, openshot.CONSTANT)
    contrast_curve.AddPoint(effect_desc['end_to'], 0.0, openshot.CONSTANT)
    
    strobe_effect = openshot.Brightness(brightness_curve, contrast_curve)
    return strobe_effect


def get_nightclub_effect(effect_desc, line_type=openshot.LINEAR):
    # nightclub_effect = {'effect': 'nightclub', 'start_from': 247, 'end_to': 322}
    hue_curve = openshot.Keyframe()
    middle_frame = int((effect_desc['start_from'] + effect_desc['end_to']) / 2)
    hue_curve.AddPoint(effect_desc['start_from'], 0.0, line_type)
    hue_curve.AddPoint(middle_frame, 1.0, line_type)
    hue_curve.AddPoint(effect_desc['end_to'], 0.0, line_type)
    nightclub_effect = openshot.Hue(hue_curve)
    return nightclub_effect


def get_earthquake_effect(effect_desc, line_type=openshot.LINEAR):
    # earthquake_effect = {'effect': 'earthquake', 'direction': 'x', 'frame': 416, 'dist': 0.05, 'offset': 2}
    shift_dist = effect_desc['dist']
    key_frame = effect_desc['frame']
    start_frame = effect_desc['frame'] - effect_desc['offset']
    end_frame = effect_desc['frame'] + effect_desc['offset']

    unchanged_curve = openshot.Keyframe()
    unchanged_curve.AddPoint(key_frame, 0.0, openshot.CONSTANT)
    blue_shift_curve = openshot.Keyframe()
    blue_shift_curve.AddPoint(start_frame, 0.0, line_type)
    blue_shift_curve.AddPoint(key_frame, -shift_dist, line_type)
    blue_shift_curve.AddPoint(end_frame, 0.0, line_type)
    red_shift_curve = openshot.Keyframe()
    red_shift_curve.AddPoint(start_frame, 0.0, line_type)
    red_shift_curve.AddPoint(key_frame, shift_dist, line_type)
    red_shift_curve.AddPoint(end_frame, 0.0, line_type)

    earthquake_effect = None
    if effect_desc['direction'] == 'x':
        earthquake_effect = openshot.ColorShift(red_shift_curve,  # red_x
                                                unchanged_curve,  # red_y
                                                unchanged_curve,  # green_x
                                                unchanged_curve,  # green_y
                                                blue_shift_curve, # blue_x
                                                unchanged_curve,  # blue_y
                                                unchanged_curve,  # alpha_x
                                                unchanged_curve   # alpha_y
                                                )
    elif effect_desc['direction'] == 'y':
        earthquake_effect = openshot.ColorShift(unchanged_curve,  # red_x
                                                red_shift_curve,  # red_y
                                                unchanged_curve,  # green_x
                                                unchanged_curve,  # green_y
                                                unchanged_curve,  # blue_x
                                                blue_shift_curve, # blue_y
                                                unchanged_curve,  # alpha_x
                                                unchanged_curve   # alpha_y
                                                )
    return earthquake_effect


def get_fancy_effects(fancy_effect_desc_list, video):
    fancy_effects = []
    for effect in fancy_effect_desc_list:
        if effect['effect'] == 'screen_pump':
            apply_screen_pump_effect(video, effect)

        if effect['effect'] == 'strobe':
            strobe_effect = get_strobe_effect(effect)
            fancy_effects.append(strobe_effect)

        if effect['effect'] == 'earthquake':
            earthquake_effect = get_earthquake_effect(effect)
            fancy_effects.append(earthquake_effect)

        if effect['effect'] == 'nightclub':
            nightclub_effect = get_nightclub_effect(effect)
            fancy_effects.append(nightclub_effect)

    return fancy_effects
