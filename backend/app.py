from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi

from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi
import boto3
# JWT 인증
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# .env파일 로드
load_dotenv()

s3_client = boto3.client(
    's3',
    region_name=os.environ.get('AWS_REGION')
)

BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
REGION = os.environ.get('AWS_REGION')

def upload_image_to_s3(file, filename): # file : 사용자가 올린파일, filename : S3에 저장될 이름
    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        filename,
        ExtraArgs={"ContentType": file.content_type}
    )
    return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{filename}"

app = Flask( 
    # front폴더로 나누어서 Flask에서 templates, static을 찾게되면 backend/templates 등으로 찾게되서 경로 오류 발생함
    __name__, 
    template_folder="../front/templates",
    static_folder="../front/static"
)

#실제 운영환경 안전하게 관리 필요
app.config["JWT_SECRET_KEY"] = "your-super-secret-key"
jwt = JWTManager(app)

# os.environ.get으로 .env에 넣은 변수명 가져오기
mongo_uri = os.environ.get('MONGO_URI')

# 인증서 파일 경로 문자열 리턴
ca = certifi.where()

# MongoDB 클러스터 연결
client = MongoClient(mongo_uri, tlsCAFile=ca) # 인증서 검증시 ca에 담아둔 경로 사용
db = client["JM"]
collection = db["users"]

tags_collection = db["tags"]


# 시작 메인 페이지
@app.route('/')
def mainpage():
    return render_template('main.html')


@app.route('/maketags', methods=['GET'])
def makeTag():
    tagData = list(tags_collection.find({}, {"_id":0}))
    print(tagData)
    return jsonify(tagData)


@app.route('/makeCard/jungle', methods=['GET'])
def makeCard():
    userData = list(collection.find({}, {
        "_id":0, 
        "desc":0,
        "password":0
        }))
    # 딕셔너리에서 password필드 제거
    return jsonify(userData)

# 로그인 페이지 - 중복확인
@app.route('/login', methods=['GET'])
def loginGet():
    return render_template('')

@app.route('/login', methods=['POST'])
def login():
    return render_template('login.html')

# 회원가입페이지
@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    return render_template('signup.html')

# 프로필확인 페이지 - 사용자 -> 다른사용자 프로필 확인
@app.route('/profile', methods=['GET'])
def profilePage():
    return render_template('Profile.html')

# 나의회원정보 확인
@app.route('/description', methods=['POST'])
def descriptionPage():
    return render_template('')

# 회원정보수정
@app.route('/rewriteProfile', methods=['POST'])
def reWrite():
    return render_template('')


if __name__ == '__main__':
    app.run(debug=True, port=3000)

    
