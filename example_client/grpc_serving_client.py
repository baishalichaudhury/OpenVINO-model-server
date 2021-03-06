#
# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from grpc.beta import implementations
import numpy as np
import tensorflow.contrib.util as tf_contrib_util
import classes
import datetime
import argparse
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

parser = argparse.ArgumentParser(description='Do requests to ie_serving and tf_serving using images in numpy format')
parser.add_argument('--images_numpy_path', required=True, help='numpy in shape [n,w,h,c]')
parser.add_argument('--grpc_address',required=False, default='localhost',  help='Specify url to grpc service. default:localhost')
parser.add_argument('--grpc_port',required=False, default=9000, help='Specify port to grpc service. default: 9000')
parser.add_argument('--input_name',required=False, default='input', help='Specify input tensor name. default: input')
parser.add_argument('--output_name',required=False, default='resnet_v1_50/predictions/Reshape_1', help='Specify output name. default: resnet_v1_50/predictions/Reshape_1')
parser.add_argument('--transpose_input', choices=["False", "True"], default="True",
                    help='Set to False to skip NHWC->NCHW input transposing. default: True',
                    dest="transpose_input",)
parser.add_argument('--iterations', default=0,
                    help='Number of requests iterations, as default use number of images in numpy memmap. default: 0 (consume all frames)',
                    dest='iterations', type=int)
# If input numpy file has too few frames according to the value of iterations and the batch size, it will be
# duplicated to match requested number of frames
parser.add_argument('--batchsize', default=1,
                    help='Number of images in a single request. default: 1',
                    dest='batchsize')
parser.add_argument('--model_name', default='resnet', help='Define model name, must be same as is in service. default: resnet',
                    dest='model_name')
args = vars(parser.parse_args())

channel = implementations.insecure_channel(args['grpc_address'], int(args['grpc_port']))

stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
processing_times = np.zeros((0),int)
imgs = np.load(args['images_numpy_path'], mmap_mode='r', allow_pickle=False)
batch_size = int(args.get('batchsize'))

iterations = int((imgs.shape[0]//batch_size) if not (args.get('iterations') or args.get('iterations') != 0) else args.get('iterations'))

while iterations * batch_size > imgs.shape[0]:
    imgs = np.append(imgs, imgs, axis=0)

print('Start processing:')
print('\tModel name: {}'.format(args.get('model_name')))
print('\tIterations: {}'.format(iterations))
print('\tImages numpy path: {}'.format(args.get('images_numpy_path')))
print('\tImages in shape: {}\n'.format(imgs.shape))

if args.get('transpose_input') == "True":
    imgs = imgs.transpose((0,3,1,2))
iteration = 0
for x in range(0, imgs.shape[0] - batch_size, batch_size):
    iteration += 1
    if iteration > iterations: break
    request = predict_pb2.PredictRequest()
    request.model_spec.name = args.get('model_name')
    img = imgs[x:(x + batch_size)]
    request.inputs[args['input_name']].CopyFrom(tf_contrib_util.make_tensor_proto(img, shape=(img.shape)))
    start_time = datetime.datetime.now()
    result = stub.Predict(request, 10.0) # result includes a dictionary with all model outputs
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds() * 1000
    processing_times = np.append(processing_times,np.array([int(duration)]))
    output = tf_contrib_util.make_ndarray(result.outputs[args['output_name']])

    nu = np.array(output)
    # for object classification models show imagenet class
    print('Iteration {}; Processing time: {:.2f} ms; speed {:.2f} fps'.format(iteration,round(np.average(duration), 2),
                                                                round(1000 * batch_size / np.average(duration), 2)
                                                                ))
    # Comment out this section for non imagenet datasets
    print("imagenet top results in a single batch:")
    for i in range(nu.shape[0]):
        single_result = nu[[i],...]
        ma = np.argmax(single_result)
        print("\t",i, classes.imagenet_classes[ma])
    # Comment out this section for non imagenet datasets

print('\nprocessing time for all iterations')
print('average time: {:.2f} ms; average speed: {:.2f} fps'.format(round(np.average(processing_times), 2),
                                                                    round(1000 * batch_size / np.average(processing_times), 2)))

print('median time: {:.2f} ms; median speed: {:.2f} fps'.format(round(np.median(processing_times), 2),
                                                                  round(1000 * batch_size / np.median(processing_times), 2)))

print('max time: {:.2f} ms; min speed: {:.2f} fps'.format(round(np.max(processing_times), 2),
                                                            round(1000 * batch_size / np.max(processing_times), 2)))

print('min time: {:.2f} ms; max speed: {:.2f} fps'.format(round(np.min(processing_times), 2),
                                                            round(1000 * batch_size / np.min(processing_times), 2)))

print('time percentile 90: {:.2f} ms; speed percentile 90: {:.2f} fps'.format(
    round(np.percentile(processing_times, 90), 2),
    round(1000 * batch_size / np.percentile(processing_times, 90), 2)
))
print('time percentile 50: {:.2f} ms; speed percentile 50: {:.2f} fps'.format(
    round(np.percentile(processing_times, 50), 2),
    round(1000 * batch_size / np.percentile(processing_times, 50), 2)
    ))
print('time standard deviation: {:.2f}'.format(round(np.std(processing_times), 2)))
print('time variance: {:.2f}'.format(round(np.var(processing_times), 2)))
