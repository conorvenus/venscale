import redis
import boto3
import os
import dotenv
import subprocess

dotenv.load_dotenv()

session = boto3.Session()

s3 = session.client(
    service_name='s3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    aws_session_token=None,
    config=boto3.session.Config(signature_version='s3v4'),
    verify=False
)

redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

def build(id):
    repo_path = os.path.join("repos", id)
    if os.path.exists(repo_path):
        try:
            os.chdir(repo_path)
            subprocess.run(["npm", "install"], shell=True, check=True)
            subprocess.run(["npm", "run", "build"], shell=True, check=True)
            if not os.path.exists("dist"):
                raise Exception("Build failed: dist folder not found.")
            for root, _, files in os.walk("dist"):
                for file in files:
                    s3.upload_file(os.path.join(root, file), "testbucket", f"builds/{id}/{file}")
        except Exception as e:
            print(f"An error occurred while building the project {id}: {e}")
        finally:
            os.chdir("../../")
    else:
        print(f"Repository path {repo_path} does not exist.")

def deploy(id):
    for file in s3.list_objects_v2(Bucket="testbucket", Prefix=f"repos/{id}")["Contents"]:
        if not os.path.exists(os.path.dirname(file["Key"])):
            os.makedirs(os.path.dirname(file["Key"]))
        s3.download_file("testbucket", file["Key"], file["Key"])
    build(id)

while True:
    id = redis.rpop("completed_uploads")
    if id is not None:
        deploy(id)