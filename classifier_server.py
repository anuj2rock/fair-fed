import glob
import os
import tensorflow as tf
import numpy as np
from xmlrpc.server import SimpleXMLRPCServer
import time
import io
import socket
import struct
from PIL import Image
import base64
import traceback
from time import sleep
import netifaces as ni
ni.ifaddresses('wlan0')
ip = ni.ifaddresses('wlan0')[2][0]['addr']
#print("listening at "+ip.strip()+":8000")
sess= tf.Session()
label_lines = []
softmax_tensor = None
server = SimpleXMLRPCServer(('192.168.43.12', 9009),allow_none=True)

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
def load_ai_server():
    #print("load_ai_server ....")
    load_start_time = time.time()
    server_socket = socket.socket()
    server_socket.bind(('192.168.43.12', 8000))
    server_socket.listen(0)
    #print("load_ai_server done")
    # socket connection live at ....1.4 @ port 8000
    # accept socket connection and listen to pakcet daata
    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    imageList = []
    try:
        while True:
            #print("waiting for hit from picamclient....")
            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                print("Images fed to AI engine ",len(imageList))
                return (process_ai_engine(imageList))
                #print("TIME taken >> ",str(( time.time() - load_start_time)))
                del imageList[:]
                #print("after processing list size>>> ",len(imageList))
                break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # image_path.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            image_stream.seek(0)
            image = Image.open(image_stream)
            imageList.append(image)
            
    except Exception as e:
    	print("Exception >> ",e)
    finally:
        connection.close()
        server_socket.close()
def close_stream_server():
    connection.close()
    server_socket.close()

def load_ai_engine():# MAJOR PERFORMANCE BOOST- does persist tf session so that session is not loaded on-demand
	print("loading AI engine...")
	global label_lines
	label_lines = [line.rstrip() for line in tf.gfile.GFile("/home/airig/python-scripts/birdfeeder/labels.txt")]
	with tf.gfile.FastGFile("/home/airig/python-scripts/birdfeeder/retrained_graph_birdfeeder.pb", 'rb') as f:#retrain_lastlayer/output_graph.pb
	    graph_def = tf.GraphDef()
	    graph_def.ParseFromString(f.read())
	    _ = tf.import_graph_def(graph_def, name='')
	global sess
	with tf.Session() as sess:
		global softmax_tensor
		softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
		print("AI engine loaded")
		#return sess,label_lines,softmax_tensor
def process_ai_engine(imageList):#(sess,label_lines,softmax_tensor):
	print('Inside AI Engine....READING Image>>>>> ')
	start_time = time.time()
	detected_obj_list=[]
	for image in imageList:
		try:
			image_array = np.array(image)[:,:,0:3]
			predictions = sess.run(softmax_tensor, {'DecodeJpeg:0': image_array})
		except Exception:
			print("error in running tf session >> ", str(traceback.print_exc()))
		top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
		human_string = label_lines[top_k[0]]
		score = predictions[0][top_k[0]]
		if(score>0.5):# 50% accuracy is VERY LINIENT!! this value needs to be adjusted as per trained model accuracy
			detected_obj_list.append(human_string)
		else:
			pass#print("score less then 0.5 for",human_string)
	try:
		human_string = max(set(detected_obj_list), key=detected_obj_list.count)
	except Exception as e:
		human_string= "UNKNOWN"
		#confidence= "UNKNOWN"
		print("Not sure. Retry.")
	return human_string#"Outcome >> "+human_string+">>(INFERENCE TIME:)"+str(( time.time() - start_time))#+">>(Confidence:)"+str(score*100)+
	
try:
	#print("with try")
	server.register_function( load_ai_engine )
	server.register_function( load_ai_server )
	server.register_introspection_functions()
	print("listening at "+ip+":9009 ................. ")
	server.serve_forever()
except(Exception,KeyboardInterrupt, SystemExit) as e:
	print("\nGPU module shutdown successfuly\n",str(e))

