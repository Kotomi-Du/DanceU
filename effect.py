from utility import edit_video, make_effect_point_list_from_desc_new

def gen_effects(effect_desc_list_new, 
                video_in_path="/home/openshot/DanceU/resources_video/spring_origin.mp4", 
                video_out_path="./spring_out.mp4", 
                frame_delta=10, 
                save_from=0, 
                save_to=None):
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

    gen_effects(effect_desc_list_new)
    