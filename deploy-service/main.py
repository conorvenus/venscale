import redis
import boto3
import os
import dotenv
import subprocess

dotenv.load_dotenv()

session = boto3.Session()

s3 = session.client(
    service_name='s3',
    endpoint_url=os.environ['S3_URL'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    aws_session_token=None,
    config=boto3.session.Config(signature_version='s3v4')
)

redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

def build(id):
    repo_path = os.path.join("repos", id)
    if os.path.exists(repo_path):
        try:    
            os.chdir(repo_path)
            subprocess.run(["npm", "install"], shell=False, check=True)
            subprocess.run(["npm", "run", "build"], shell=False, check=True)
            if not os.path.exists("dist"):
                raise Exception("Build failed: dist folder not found.")
            for root, _, files in os.walk("dist"):
                for file in files:
                    s3.upload_file(os.path.join(root, file), "venscale", f"builds/{id}/{file}")
            redis.set(id, "deployed")
        except Exception as e:
            print(f"An error occurred while building the project {id}: {e}")
            redis.set(id, "failed")
        finally:
            os.chdir("../../")
    else:
        print(f"Repository path {repo_path} does not exist.")

def deploy(id):
    for file in s3.list_objects_v2(Bucket="venscale", Prefix=f"repos/{id}")["Contents"]:
        if not os.path.exists(os.path.dirname(file["Key"])):
            os.makedirs(os.path.dirname(file["Key"]))
        s3.download_file("venscale", file["Key"], file["Key"])
    build(id)

redis.delete("completed_uploads")

while True:
    id = redis.rpop("completed_uploads")
    if id is not None:
        redis.set(id, "deploying")
        deploy(id)