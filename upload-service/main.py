from flask import Flask, request, jsonify
from git import Repo
import threading
import uuid
import os
import boto3
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app
)

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

redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_files(dir):
    files = []
    for root, _, filenames in os.walk(dir):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def clone_repo(repo_url, id):
    try:
        Repo.clone_from(repo_url, f"repos/{id}")
        for file in get_files(f"repos/{id}"):
            if ".git" in file:
                continue
            file = file.replace("\\", "/")
            s3.upload_file(file, "venscale", file)
            print(f"Uploaded {file}")
            os.remove(file)
        redis.set(id, "uploaded")
        redis.lpush("completed_uploads", id)
    except Exception as e:
        redis.set(id, "failed")

def get_uuid():
    return str(uuid.uuid4())

@app.route("/deploy", methods=['GET'])
@limiter.limit("1 per 10 seconds")
def deploy():
    repo_url = request.args.get('repoUrl')
    if not repo_url:
        return jsonify({"error": "No repoUrl provided"}), 400
    id = get_uuid()
    redis.set(id, "uploading")
    threading.Thread(target=clone_repo, args=(repo_url, id)).start()
    return jsonify({"id": id}), 200

@app.route("/status", methods=['GET'])
@limiter.limit("1 per second")
def status():
    id = request.args.get('id')
    if not id:
        return jsonify({"error": "No id provided"}), 400
    if redis.exists(id):
        return jsonify({"status": redis.get(id)}), 200
    return jsonify({"error": "No deployment found with the provided id"}), 404

if __name__ == "__main__":
    app.run(debug=True)