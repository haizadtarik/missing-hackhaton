import time
import requests
import boto3
import cv2
import json

# =========== Setup bot ============
TOKEN = '<BOT_API_TOKEN>'
bot = "https://api.telegram.org/bot"+TOKEN+"/"
file_url = 'https://api.telegram.org/file/bot'+TOKEN+'/'

# ======== Connect to AWS ========
rekogAPI = boto3.client('rekognition',
        region_name = '<REGION_NAME>', 
        aws_access_key_id = '<AWS_ACCESS_KEY_ID',
        aws_secret_access_key = '<AWS_SECRET_ACCESS_KEY>')

s3 = boto3.client('s3',
        region_name = '<REGION_NAME>', 
        aws_access_key_id = '<AWS_ACCESS_KEY_ID',
        aws_secret_access_key = '<AWS_SECRET_ACCESS_KEY>')

def send_message(chat, reply_text):
    params = {'chat_id': chat, 'text': reply_text}
    response = requests.post(bot + 'sendMessage', data=params)
    return response

camera = cv2.VideoCapture(0)

while(True):
    found_list = json.loads(s3.get_object(Bucket='<BUCKET_NAME2>',Key='<JSON_FILE>')['Body'].read())
    # ------- Camera 1 ------
    _ , frame = camera.read()    
    # Preprocess input
    height, width, channels = frame.shape
    target_img = cv2.imencode('.jpg', frame)[1].tostring()
    # Detecting face
    face_flag = rekogAPI.detect_faces(Image={'Bytes':target_img})
    print('Number of face detected from web stream: ', len(face_flag['FaceDetails']))
    if len(face_flag['FaceDetails']) > 0:
        resp = s3.list_objects_v2(Bucket='missingperson')
        if resp['KeyCount'] > 0:
            for obj in resp['Contents']:
                # compare faces and recognizing face
                response = rekogAPI.compare_faces(SourceImage={'S3Object': {'Bucket': '<BUCKET_NAME>', 'Name': obj['Key']}}, TargetImage={ 'Bytes': target_img })
                if len(response['FaceMatches']) > 0:
                    if response['FaceMatches'][0]['Similarity'] > 80.0:
                        # process output
                        x = int(response['FaceMatches'][0]['Face']['BoundingBox']['Left']*width)
                        y = int(response['FaceMatches'][0]['Face']['BoundingBox']['Top']*height)
                        w = int(response['FaceMatches'][0]['Face']['BoundingBox']['Width']*width)
                        h = int(response['FaceMatches'][0]['Face']['BoundingBox']['Height']*height)

                        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),3)
                        chat_id = obj['Key']
                        if chat_id in found_list.keys():
                            continue
                        else:
                            print('Person found by Camera 1 at https://www.google.com/maps/search/?api=1&query=3.1390,101.6869')
                            found_list[chat_id] = 'The person has been found by Camera 1 at https://www.google.com/maps/search/?api=1&query=3.1390,101.6869'
                            s3.put_object(Body=json.dumps(found_list), Bucket='<BUCKET_NAME2>', Key='<JSON_FILE>')
                            send_message(chat_id, found_list[chat_id])                        
           

    # Display video stream
    cv2.imshow('frame',frame)
    
    # Reduce stress to processor
    time.sleep(0.1) 

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()