import io
import socket
import struct
import time
import picamera

# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
def stream_to_ai_server():
    client_socket = socket.socket()
    connected = False
    while connected is False:
        try:
            client_socket.connect(('192.168.43.12', 8000))
            connected = True
            #print("CONNECTED 12:8000")
        except ConnectionRefusedError:
            print("Streaming.....")#print("retry connecting....port 12:8000")
            pass
    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    try:
        camera = picamera.PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 30
        #camera.iso = 600
        # camera.resolution = (640, 480)
        # Start a preview and let the camera warm up for 2 seconds
        #camera.start_preview()
        #time.sleep(0.1)

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep
        # our protocol simple)
        start = time.time()
        stream = io.BytesIO()
        for foo in camera.capture_continuous(stream, 'jpeg',use_video_port=True):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
            #print("CONN ::IMAGE CAPTURED")
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            # Rewind the stream and send the image data over the wire
            stream.seek(0)
            connection.write(stream.read())
            # If we've been capturing for more than 30 seconds, quit
            if time.time() - start > 0.5:
                break
            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
        # Write a length of zero to the stream to signal we're done
        connection.write(struct.pack('<L', 0))
        camera.close()
        #print("END OF SIGNAL SENT")
    finally:
        close_client_stream(connection,client_socket)
        #print("inside finally...")#client_socket.close()
def close_client_stream(connection,client_socket):
    connection.close()
    client_socket.close()
    print("PiCAM Streaming DONE")
#stream_to_ai_server()
