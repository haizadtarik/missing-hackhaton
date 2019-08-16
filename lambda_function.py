import json
from botocore.vendored import requests
import boto3

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

def upload_photo(photo_url, user_id):
    photo = requests.get(photo_url)
    face_flag = rekogAPI.detect_faces(Image={'Bytes':photo.content})
    if len(face_flag['FaceDetails']) > 0:
        s3.put_object(Bucket="<BUCKET_NAME>", Key = str(user_id), Body=photo.content)
        upload_flag = 'success'
    else:
        upload_flag = 'failed'
    return upload_flag
    
def send_message(chat, reply_text):
    params = {'chat_id': chat, 'text': reply_text}
    response = requests.get(bot + 'sendMessage', data=params)
    
def lambda_handler(event, context):
    found_list = json.loads(s3.get_object(Bucket='<BUCKET_NAME2>',Key='<JSON_FILE>')['Body'].read())
    # ------ Read Message ------
    results = json.loads(event['body'])
    chat_id = results['message']['chat']['id']
    if 'photo' in results['message'].keys():
        index = len(results['message']['photo']) - 1 
        file_id = results['message']['photo'][index]["file_id"]
        file_info = requests.get(bot + 'getFile', params={"chat_id": chat_id, "file_id": file_id})
        file_path = file_info.json()['result']['file_path']
        message = file_url + file_path
        upload = upload_photo(message, chat_id)
        if upload == 'failed':
            reply = 'Can\'t detect face. Plsease send another picture'
            send_message(chat_id, reply)
        else:
            reply = 'Image added to database'
            send_message(chat_id, reply)
    elif 'text' in results['message'].keys(): 
        message = results['message']['text']
        if message == '/start':
            reply = 'Hi! I am Rescuer Bot.\nSend /report to report missing person.'
            send_message(chat_id, reply)
        elif message == '/report':
            if chat_id in found_list.keys():
                del found_list[str(chat_id)]
                reply = 'Please send the picture of the missing person'
                send_message(chat_id, reply)
            else:
                reply = 'Please send the picture of the missing person'
                send_message(chat_id, reply)
        elif message == '/status':
            if str(chat_id) in found_list.keys():
                send_message(chat_id, found_list[str(chat_id)])
            else:
                reply = 'Not Found yet'
                send_message(chat_id, reply)
        elif message == '/close':
            if chat_id in found_list.keys():
                del found_list[str(chat_id)]
                s3.delete_object(Bucket='<BUCKET_NAME>', Key=str(chat_id))
                reply = 'Report has been close.'
                send_message(chat_id, reply)
            else:
                reply = 'Sorry the person haven\'t been found'
                send_message(chat_id, reply)    
        elif message == '/help':
            reply = 'Send /report to report missing person or just send the picture of the missing person.\nSend /status to check the status of the case reported\nSend /close to lose reported missing case'
            send_message(chat_id, reply)
        else:
            reply = 'Invalid input. Please send the picture of the missing person'
            send_message(chat_id, reply)        
    else: 
        reply = 'Invalid input type'
        send_message(chat_id, reply)

    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }