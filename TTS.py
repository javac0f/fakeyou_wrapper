import requests
import json
import time
from uuid import uuid4


# LOAD API ENDPOINTS
endpoint_urls = {
    "base": "https://api.fakeyou.com/",
    "Voice_List":"https://api.fakeyou.com/tts/list",
    "TTS_request":'https://api.fakeyou.com/tts/inference',
    "audio_output":"https://storage.googleapis.com/vocodes-public"
}


def get_voicelist():
    response = requests.get(url = endpoint_urls['Voice_List'])
    return response, 200 


def write_voicelist(filename = "voices.txt"):
    f = open(file=filename, mode = "w")
    f.write(json.dumps(get_voicelist().json()))
    f.close()


def submit_job(inference_text:str, tts_model_token:str = "TM:7egqdjvs23pr"):    

    # OTHER MODEL TOKENS:
    #TM:nw83aje8x4em


    payload = {"tts_model_token":tts_model_token, "uuid_idempotency_token": str(uuid4()),"inference_text":inference_text}
    response = requests.post(url = endpoint_urls["TTS_request"], json = payload)

    print("submitted job status: " + str(response.status_code))
    
    return response.status_code, response.json()['inference_job_token']


def poll_for_completion(inference_job_token:str):
    response = requests.get(url = "https://api.fakeyou.com/tts/job/" + inference_job_token)
    poll_status:str = response.json()['state']['status']
    
    print()
    print("poll for completion response: " + str(response))
    print(poll_status)
    print()

    try: voicefile_url:str = endpoint_urls['audio_output'] + response.json()['state']['maybe_public_bucket_wav_audio_path']
    except: voicefile_url = None
    finally: return poll_status, voicefile_url

def get_voicefile(voicefile_url, voicefile_out = 'testing.wav'):
    file = requests.get(url = voicefile_url, allow_redirects=True)
    open(voicefile_out, 'wb').write(file.content)


def say(text:str, output_filename:str = 'out.wav'):
    job = submit_job(inference_text=text)
    # job[0] = status code
    # job[1] = inference token

    if(job[0] == 200):
        i = 0
        while(True):
            poll = poll_for_completion(inference_job_token=job[1])
            print('polled ' + str(i))
            print(poll[0])
            print()

            # WAIT FOR JOB TO BE DONE
            if(poll[0] == 'complete_success'): 
                break
            elif(i > 10): 
                return Exception ("Timed Out")    # timeout if taking too long (to avoid loops)
            else: 
                i+= 1
                time.sleep(5) # try again in 5 seconds

        # IF JOB IS DONE
        get_voicefile(voicefile_url=poll[1], voicefile_out=output_filename)

