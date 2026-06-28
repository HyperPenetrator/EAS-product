import urllib.request
import urllib.parse
import json
import uuid
import time
import os

def upload_file(url, file_path):
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
    
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        'Content-Type: text/csv\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def get_job_status(url):
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode('utf-8'))

if __name__ == '__main__':
    upload_url = 'http://localhost:5000/api/upload'
    file_path = 'sample_data.csv'
    print(f"Uploading {file_path} to {upload_url}...")
    try:
        res = upload_file(upload_url, file_path)
        job_id = res['job_id']
        print(f"Upload successful! Job ID: {job_id}")
        
        status_url = f'http://localhost:5000/api/job/{job_id}'
        while True:
            job = get_job_status(status_url)
            status = job['status']
            progress = job['progress']
            print(f"Status: {status} | Progress: {progress}%")
            if status in ['complete', 'error']:
                if status == 'complete':
                    print("[SUCCESS] Processing completed successfully!")
                    print("KPI Results:")
                    print(json.dumps(job.get('results'), indent=2))
                else:
                    print(f"[ERROR] Processing failed: {job.get('error_message')}")
                break
            time.sleep(1)
    except Exception as e:
        print(f"Error during upload/processing: {e}")
