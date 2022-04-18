import cv2
import os
import numpy as np


framenum_uplimit = 800
def sample(data,framenum_uplimit) :
    new_data = []
    for v in data:
        if v < framenum_uplimit:
            new_data.append(v)
    return new_data


class Point:
    def __init__ (self, x, y):
        self.x = x
        self.y = y 
    def value(self):
        return [self.x, self.y]

def draw_text(img, text,
              font=cv2.FONT_HERSHEY_PLAIN,
              pos=(0, 0),
              font_scale=3,
              font_thickness=2,
              text_color=(0, 255, 0),
              text_color_bg=(0, 0, 0)
              ):

    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(img, pos, (x + text_w, y + text_h), text_color_bg, -1)
    cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

    return text_size

def draw_traingle(img_folder, img_idx_list, pos, label, color, radius):
    import cv2
    # draw shapes to the detection results
    for img_idx in img_idx_list:
        if img_idx is None:
            continue
        img_name='{}/{}.png'.format(img_folder, img_idx)
        img = cv2.imread(img_name)
        if img is None:
            continue
        if label == "start":
            pt1 = (pos.x - radius, pos.y-radius)
            pt2 = (pos.x + radius, pos.y)
            pt3 = (pos.x -radius, pos.y+radius) 
        if label == "end":
            pt1 = (pos.x + radius, pos.y-radius)
            pt2 = (pos.x - radius, pos.y)
            pt3 = (pos.x +radius, pos.y+radius) 

        triangle_cnt = np.array( [pt1, pt2, pt3] )
        cv2.drawContours(img, [triangle_cnt], 0, color , -1)
        cv2.imwrite(img_name, img)
    
def draw_circle_to_images(img_folder, img_idx_list, pos, radius, color):
    import cv2
    # draw shapes to the detection results
    for img_idx in img_idx_list:
        if img_idx is None:
            continue
        img_name='{}/{}.png'.format(img_folder, img_idx)
        img = cv2.imread(img_name)
        if img is None:
            continue
        cv2.circle(img, pos.value(), radius, color, -1)
        cv2.imwrite(img_name, img)


def draw_shapes_to_special_images(img_folder, start_list, key_list, end_list, beats, strong_beats=None):
    exist_and_not_empty = os.listdir(img_folder)
    if exist_and_not_empty is False:
        print('{} not exist or empty'.format(img_folder))
        return

    first_img = cv2.imread('{}/1.png'.format(img_folder))
    height = first_img.shape[0]
    width = first_img.shape[1]
    radius = int(height/8)
    pos_right_top1 = Point(width-radius, radius)
    pos_right_top2 = Point(width-radius, radius*3)
    pos_right_top3 = Point(width-radius, radius*5)
    pos_right_top4 = Point(width-radius, radius*7)

    pos_left_bottom = Point(radius, radius*7)

    # BGR values
    red = (0, 0, 255)
    orange = (0, 165, 255)
    lightcoral = (128, 128, 240) #RGB
    draw_circle_to_images(img_folder, beats, pos_left_bottom, radius, lightcoral)
    if strong_beats is not None:
        draw_circle_to_images(img_folder, strong_beats, pos_left_bottom, radius, red)
    draw_traingle(img_folder, start_list, pos_right_top2, "start", orange, radius)
    draw_circle_to_images(img_folder, key_list, pos_right_top3, radius, red)
    draw_traingle(img_folder, end_list, pos_right_top4, "end", orange, radius)


def draw_audio_feature(audio_onsets, audio_bpm, beats, group_list, title):
    import matplotlib.pyplot as plt
    if framenum_uplimit != -1:
        audio_onsets = audio_onsets[:framenum_uplimit]
        beats = sample(beats,framenum_uplimit)
        group_list = sample(group_list,framenum_uplimit)

    x_data = range(len(audio_onsets))
    figure = plt.figure(figsize=(len(audio_onsets)/35,5))
    ax = figure.add_subplot()

    #onset_length
    ax.plot(x_data, audio_onsets, color="tab:blue",label="onset" , linestyle='-')

    #beat per minute
    textstr =  "BPM = {:.2f}".format(audio_bpm)
    props = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)
    ax.text(1.05, 0.05, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

    #beat
    for beat in beats:
        if beat in group_list:  # group boundaries
            plt.axvline(x=beat, color='lightcoral', label = "group boundary",linestyle='--')
        else:
            plt.axvline(x=beat, color='mistyrose', label = "music beat", linestyle='--')

    #legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left", bbox_to_anchor=(1.05, 1.0))
    plt.tight_layout()
    if not os.path.exists("vis_result") :
        os.mkdir("vis_result")
    figure.savefig("vis_result/{}_audio.png".format(title))

def draw_decision_statistics(area_data, start_list, key_list, end_list, title, beats, group_list, zoom_scale_list):
    import matplotlib.pyplot as plt
    import numpy as np
    if framenum_uplimit != -1:
        area_data = area_data[:framenum_uplimit]
        start_list= sample(start_list,framenum_uplimit)
        key_list = sample(key_list,framenum_uplimit)
        end_list = sample(end_list,framenum_uplimit)
        beats = sample(beats,framenum_uplimit)
        group_list = sample(group_list,framenum_uplimit)
        zoom_scale_list = zoom_scale_list[:len(key_list)]

    x_data = range(len(area_data))
    # create figure and axis objects with subplots()
    figure = plt.figure(figsize=(len(area_data)/35,5))
    ax = figure.add_subplot()

    # motion data
    ax.plot(x_data, area_data, color="green",label="motion (bbox area)" , linestyle='-')
    ax.xaxis.set_ticks(np.arange(np.min(x_data), np.max(x_data), 50))

    # audio data
    # vis_y = [area_data[i] for i in beats]
    # plt.scatter( beats, vis_y, color = "red", label = "audio", marker="x",  s = 10)

    for beat in beats:
        if beat in group_list:  # group boundaries
            plt.axvline(x=beat, color='lightcoral', label = "group boundary",linestyle='--')
        else:
            plt.axvline(x=beat, color='mistyrose', label = "music beat", linestyle='--')

    # effect data
    vis_y = [area_data[i] for i in start_list]
    ax.scatter(start_list, vis_y, color = "orange", label = "effect start frame",marker = ">", s = 50)

    vis_y = [area_data[i] for i in key_list]
    ax.scatter(key_list, vis_y, color = "red", label = "effect key frame", marker = "X", s = 75)

    # add scale info next to the key point
    for i, scale in enumerate(zoom_scale_list):
        ax.annotate(round(scale,2), (key_list[i], vis_y[i]))

    vis_y = [area_data[i] for i in end_list]
    ax.scatter(end_list, vis_y, color = "orange", label = "effect end frame",marker = "<", s = 50)

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left", bbox_to_anchor=(1.05, 1.0))
    plt.tight_layout()
    if not os.path.exists("vis_result") :
        os.mkdir("vis_result")
    figure.savefig("vis_result/{}.png".format(title))


def draw_video_property_curve(property_dict, prop_type='scale', title='name'):
    # prop_type can be 'scale', 'loc_x', 'loc_y'
    frame_idx_list = property_dict['frame']
    prop_list = property_dict[prop_type]

    import matplotlib.pyplot as plt
    figure = plt.figure(figsize=(len(frame_idx_list)/35, 5))
    ax = figure.add_subplot()

    ax.plot(frame_idx_list, prop_list, color="green",label=prop_type , linestyle='-')

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left", bbox_to_anchor=(1.05, 1.0))

    plt.tight_layout()
    if not os.path.exists("vis_result") :
        os.mkdir("vis_result")
    figure.savefig("vis_result/{}_{}.png".format(title, prop_type))


def print_performance():
    #Audio
    #Motion
    #Effect Decision
    #Video Encoding
    pass