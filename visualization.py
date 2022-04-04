import cv2
import os


def draw_circle_to_images(img_folder, img_idx_list, pos, radius, color):
    import cv2
    # draw shapes to the detection results
    for img_idx in img_idx_list:
        img_name='{}/{}.png'.format(img_folder, img_idx)
        img = cv2.imread(img_name)
        cv2.circle(img, pos, radius, color, -1)
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
    pos_right_top1 = (width-radius, radius)
    pos_right_top2 = (width-radius, radius*3)
    pos_right_top3 = (width-radius, radius*5)
    pos_right_top4 = (width-radius, radius*7)

    pos_left_bottom = (radius, radius*7)

    # BGR values
    black = (0, 0, 0)
    red = (0, 0, 255)
    green = (0, 255, 0)
    blue = (255, 0, 0)
    yellow = (0, 255, 255)
    draw_circle_to_images(img_folder, beats, pos_left_bottom, radius, yellow)
    if strong_beats is not None:
        draw_circle_to_images(img_folder, strong_beats, pos_left_bottom, radius, red)
    draw_circle_to_images(img_folder, start_list, pos_right_top2, radius, black)
    draw_circle_to_images(img_folder, key_list, pos_right_top3, radius, blue)
    draw_circle_to_images(img_folder, end_list, pos_right_top4, radius, black)


def visualization(area_data, start_list, key_list, end_list, title, beats, group_list, zoom_scale_list):
    import matplotlib.pyplot as plt
    x_data = range(len(area_data))
    # create figure and axis objects with subplots()
    fig,ax = plt.subplots()
    # motion data
    ax.plot(x_data, area_data, color="green",label="motion" , linestyle='-')

    # audio data
    # vis_y = [area_data[i] for i in beats]
    # plt.scatter( beats, vis_y, color = "red", label = "audio", marker="x",  s = 10)

    for beat in beats:
        if beat in group_list:  # group boundaries
            plt.axvline(x=beat, color='b', linestyle='--')
        else:
            plt.axvline(x=beat, color='y', linestyle='--')

    # effect data
    vis_y = [area_data[i] for i in start_list]
    plt.scatter(start_list, vis_y, color = "black", label = "start effect",s = 25)

    vis_y = [area_data[i] for i in key_list]
    plt.scatter(key_list, vis_y, color = "blue", label = "key effect", s = 25)

    # add scale info next to the key point
    for i, scale in enumerate(zoom_scale_list):
        ax.annotate(scale, (key_list[i], vis_y[i]))

    vis_y = [area_data[i] for i in end_list]
    plt.scatter(end_list, vis_y, color = "black", label = "end_effect", s = 25)

    ax.legend( loc="upper left", bbox_to_anchor=(1.05, 1.0))
    plt.tight_layout()
    if not os.path.exists("vis_result") :
        os.mkdir("vis_result")
    plt.savefig("vis_result/{}.png".format(title))


def print_performance():
    #Audio
    #Motion
    #Effect Decision
    #Video Encoding
    pass