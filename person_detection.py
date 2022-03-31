import colorsys
import logging
import random
import sys
from argparse import ArgumentParser, SUPPRESS
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from openvino.inference_engine import IECore

sys.path.append(str(Path(__file__).resolve().parents[2] / 'common/python'))


from ov_backend import models
from ov_backend.pipelines import get_user_config, AsyncPipeline
from ov_backend.images_capture import open_images_capture
from ov_backend.helpers import resolution
logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-m', '--model', help='Optional. Path to an .xml file with a trained model.',
                      default="ov_backend/model_ir/person-detection-0200.xml", type=Path)
    args.add_argument('-at', '--architecture_type', help='Optional. Specify model\' architecture type.',
                      type=str, default='ssd', choices=('ssd', 'yolo', 'yolov4', 'faceboxes', 'centernet', 'ctpn',
                                                        'retinaface', 'ultra_lightweight_face_detection',
                                                        'retinaface-pytorch'))
    args.add_argument('-d', '--device', default='CPU', type=str,
                      help='Optional. Specify the target device to infer on; CPU, GPU, HDDL or MYRIAD is '
                           'acceptable. The demo will look for a suitable plugin for device specified. '
                           'Default value is CPU.')

    common_model_args = parser.add_argument_group('Common model options')
    common_model_args.add_argument('--labels', help='Optional. Labels mapping file.', default=None, type=str)
    common_model_args.add_argument('-t', '--prob_threshold', default=0.5, type=float,
                                   help='Optional. Probability threshold for detections filtering.')
    common_model_args.add_argument('--keep_aspect_ratio', action='store_true', default=False,
                                   help='Optional. Keeps aspect ratio on resize.')
    infer_args = parser.add_argument_group('Inference options')
    infer_args.add_argument('-nireq', '--num_infer_requests', help='Optional. Number of infer requests',
                            default=0, type=int)
    infer_args.add_argument('-nstreams', '--num_streams',
                            help='Optional. Number of streams to use for inference on the CPU or/and GPU in throughput '
                                 'mode (for HETERO and MULTI device cases use format '
                                 '<device1>:<nstreams1>,<device2>:<nstreams2> or just <nstreams>).',
                            default='', type=str)
    infer_args.add_argument('-nthreads', '--num_threads', default=None, type=int,
                            help='Optional. Number of threads to use for inference on CPU (including HETERO cases).')
    
    io_args = parser.add_argument_group('Input/output options')
    io_args.add_argument('--loop', default=False, action='store_true',
                         help='Optional. Enable reading the input in a loop.')
    io_args.add_argument('-o', '--output', required=False,
                         help='Optional. Name of the output file(s) to save.')
    io_args.add_argument('-limit', '--output_limit', required=False, default=1000, type=int,
                         help='Optional. Number of frames to store in output. '
                              'If 0 is set, all frames are stored.')
    io_args.add_argument('--no_show', help="Optional. Don't show output.", action='store_false')
    io_args.add_argument('--output_resolution', default=None, type=resolution,
                         help='Optional. Specify the maximum output window resolution '
                              'in (width x height) format. Example: 1280x720. '
                              'Input frame size used by default.')
    io_args.add_argument('-u', '--utilization_monitors', default='', type=str,
                         help='Optional. List of monitors to show initially.')

    input_transform_args = parser.add_argument_group('Input transform options')
    input_transform_args.add_argument('--reverse_input_channels', default=False, action='store_true',
                                      help='Optional. Switch the input channels order from '
                                           'BGR to RGB.')
    input_transform_args.add_argument('--mean_values', default=None, type=float, nargs=3,
                                      help='Optional. Normalize input by subtracting the mean '
                                           'values per channel. Example: 255 255 255')
    input_transform_args.add_argument('--scale_values', default=None, type=float, nargs=3,
                                      help='Optional. Divide input by scale values per channel. '
                                           'Division is applied after mean values subtraction. '
                                           'Example: 255 255 255')
 
    return parser

def get_model(ie, args):
    input_transform = models.InputTransform(args.reverse_input_channels, args.mean_values, args.scale_values)
    common_args = (ie, args.model, input_transform)
    return models.SSD(*common_args, labels=args.labels, keep_aspect_ratio_resize=args.keep_aspect_ratio)

def Infer(input_path):
    bboxes = []
    args = build_argparser().parse_args()
    log.info('Initializing Inference Engine...')
    ie = IECore()

    plugin_config = get_user_config(args.device, args.num_streams, args.num_threads)

    log.info('Loading network...')

    model = get_model(ie, args)

    detector_pipeline = AsyncPipeline(ie, model, plugin_config,
                                      device="CPU", max_num_requests=0)

    cap = open_images_capture(input_path, args.loop)

    next_frame_id = 0
    next_frame_id_to_show = 0

    log.info('Starting inference...')

    while True:
        if detector_pipeline.callback_exceptions:
            raise detector_pipeline.callback_exceptions[0]
        # Process all completed requests
        results = detector_pipeline.get_result(next_frame_id_to_show)
        if results:
            detections, frame_meta = results
            frame = frame_meta['frame']
            start_time = frame_meta['start_time']

            size = frame.shape[:2]
            for detection in detections:
                if detection.score > args.prob_threshold:
                    xmin = max(int(detection.xmin), 0)
                    ymin = max(int(detection.ymin), 0)
                    xmax = min(int(detection.xmax), size[1])
                    ymax = min(int(detection.ymax), size[0])
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0,250,0), 2)
                    cv2.putText(frame, '{} {:.1%}'.format("person", detection.score),
                        (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0,250,0), 1)
                    bboxes.append([xmin, ymin, xmax,ymax])
                    break

            next_frame_id_to_show += 1

            if not args.no_show:
                cv2.imshow('Detection Results', frame)
                #cv2.imwrite("D:\\pose_data\\output\\"+str(next_frame_id_to_show)+".png",frame)
                key = cv2.waitKey(1)
                ESC_KEY = 27
                # Quit.
                if key in {ord('q'), ord('Q'), ESC_KEY}:
                    break
            continue

        if detector_pipeline.is_ready():
            # Get new image/frame
            start_time = perf_counter()
            frame = cap.read()
            
            if frame is None:
                if next_frame_id == 0:
                    raise ValueError("Can't read an image from the input")
                break
            x,y = frame.shape[0:2]
            frame = cv2.resize(frame,(int(y/3), int(x/3)) )
            if next_frame_id == 0:
                output_transform = models.OutputTransform(frame.shape[:2], args.output_resolution)
            # Submit for inference
            detector_pipeline.submit_data(frame, next_frame_id, {'frame': frame, 'start_time': start_time})
            next_frame_id += 1

        else:
            # Wait for empty request
            detector_pipeline.await_any()

    detector_pipeline.await_all()
    # Process completed requests
    for next_frame_id_to_show in range(next_frame_id_to_show, next_frame_id):
        results = detector_pipeline.get_result(next_frame_id_to_show)
        while results is None:
            results = detector_pipeline.get_result(next_frame_id_to_show)
        detections, frame_meta = results
        frame = frame_meta['frame']
        start_time = frame_meta['start_time']


        size = frame.shape[:2]
        for detection in detections:
            if detection.score > args.prob_threshold:
                xmin = max(int(detection.xmin), 0)
                ymin = max(int(detection.ymin), 0)
                xmax = min(int(detection.xmax), size[1])
                ymax = min(int(detection.ymax), size[0])
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0,250,0), 2)
                cv2.putText(frame, '{} {:.1%}'.format("person", detection.score),
                    (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0,250,0), 1)

        if not args.no_show:
            cv2.imshow('Detection Results', frame)
            #cv2.imwrite("D:\\pose_data\\output\\"+str(next_frame_id)+".png",frame)
            key = cv2.waitKey(1)

            ESC_KEY = 27
            # Quit.
            if key in {ord('q'), ord('Q'), ESC_KEY}:
                break
    return bboxes


if __name__ == '__main__':
    sys.exit(Infer("resources_video/spring_origin.mp4") or 0)