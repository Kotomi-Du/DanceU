from utility import edit_video, make_effect_point_list_from_desc_new

def gen_effects(effect_desc_list_new, 
                video_in_path="/home/openshot/DanceU/resources_video/spring_origin.mp4", 
                video_out_path="./spring_out_0320.mp4", 
                frame_delta=10, 
                save_from=0, 
                save_to=600):
    effect_point_list = make_effect_point_list_from_desc_new(effect_desc_list_new, frame_delta=frame_delta)
    edit_video(video_in_path=video_in_path, 
                video_out_path=video_out_path, 
                effect_point_list=effect_point_list,
                save_from=save_from,
                save_to=save_to)

if __name__ == '__main__':
    # format of effect list:
    effect_desc_list_new =[{
        'frame':53, 
        'effect':[{'type':'zoom', 'scale':-0.2}, {'type':'move', 'location_x':-0.1}],
        'start_from':43,
        'end_to': None
        },{
        'frame':73, 
        'effect':[{'type':'zoom', 'scale':0.2}],
        'start_from':None,
        'end_to': None
        }
    ]


    effect_desc_list_new = [{'frame': 69, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 59, 'end_to': 88}, {'frame': 133, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 121, 'end_to': 147}, {'frame': 191, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 167, 'end_to': 218}, {'frame': 278, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 269, 'end_to': 294}, {'frame': 418, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 408, 'end_to': 429}, {'frame': 494, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 489, 'end_to': 508}, {'frame': 576, 'effect': [{'type': 'zoom', 'scale': 1.35}], 'start_from': 558, 'end_to': 603}]
    gen_effects(effect_desc_list_new)
    