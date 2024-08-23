from flask import Flask, request, send_file
import boto3
import os
import tldextract
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

session = boto3.Session()

s3 = session.client(
    service_name='s3',
    endpoint_url=os.environ['S3_URL'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    aws_session_token=None,
    config=boto3.session.Config(signature_version='s3v4'),
    verify=False
)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get(path):
    if not path or path == '/':
        path = "index.html"
    host = tldextract.extract(request.host)
    if not host.subdomain or '.' in host.subdomain:
        return f"The URL you provided does not correspond to a valid VenScale deployment!", 400
    id = host.subdomain
    objects = s3.list_objects_v2(Bucket="venscale", Prefix=f"builds/{id}")
    if "Contents" not in objects:
        return f"Deployment {id} does not exist!", 404
    files = [file["Key"] for file in objects["Contents"] if file["Key"].endswith(path.split("/")[-1])]
    if len(files) == 0:
        return f"Resource {path} does not exist in deployment {id}!", 404
    if not os.path.exists(f"cache/{id}"):
        os.makedirs(f"cache/{id}")
    if not os.path.exists(f"cache/{id}/{path.split('/')[-1]}"):
        s3.download_file("venscale", files[0], f"cache/{id}/{path.split('/')[-1]}")
    return send_file(f"cache/{id}/" + path.split("/")[-1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)