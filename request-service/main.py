from flask import Flask, request, Response, send_file
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
    s3_key = f"builds/{id}/{path.split('/')[-1]}"
    try:
        if not os.path.exists(s3_key):
            s3.download_file("venscale", s3_key, s3_key)
        return send_file(s3_key, as_attachment=False, attachment_filename=path)
    except s3.exceptions.NoSuchKey:
        return f"The file {path} was not found in the deployment with ID {id}!", 404
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)