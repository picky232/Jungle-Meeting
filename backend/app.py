from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
app.config["JWT_SECRET_KEY"] = 

# .env파일 로드
load_dotenv()

app = Flask( 
    # front폴더로 나누어서 Flask에서 templates, static을 찾게되면 backend/templates 등으로 찾게되서 경로 오류 발생함
    __name__, 
    template_folder="../front/templates",
    static_folder="../front/static"
)

# os.environ.get으로 .env에 넣은 변수명 가져오기
mongo_uri = os.environ.get('MONGO_URI')

# 인증서 파일 경로 문자열 리턴
ca = certifi.where()

# MongoDB 클러스터 연결
client = MongoClient(mongo_uri, tlsCAFile=ca) # 인증서 검증시 ca에 담아둔 경로 사용
db = client["JM"]
collection = db["users"]


# 시작 메인 페이지
@app.route('/')
def mainpage():
    collection.insert_one({"userId": "test1"})
    all_users = list(collection.find({}, {"_id": 0}))
    print(all_users)
    return render_template('main.html')

# 로그인 페이
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('')

# 회원가입페이지
@app.route('/signup', methods=['POST'])
def signUp():
    return render_template('')

# 프로필확인 페이지 - 사용자 -> 다른사용자 프로필 확인
@app.route('/profile', methods=['GET'])
def profilePage():
    return render_template('')

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
