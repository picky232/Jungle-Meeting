from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi

# JWT 인증
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# .env파일 로드
load_dotenv()

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


# 시작 메인 페이지
@app.route('/')
def mainpage():
    collection.insert_one({"userId": "test1"})
    all_users = list(collection.find({}, {"_id": 0}))
    print(all_users)
    return render_template('main.html')

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import bcrypt

#화면 전환 라우트
@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


# 1. 아이디 중복 여부 확인 API
@app.route('/checkUserid', methods=['POST'])
def check_userid():
    give_id = request.form.get('give_id')
    
    # DB에서 해당 ID 탐색
    user = db.users.find_one({'id': give_id})
    
    if user:
        # 2. 중복인 경우
        return jsonify({'exists': True})
    else:
        # 3. 중복이 아닌 경우
        return jsonify({'exists': False})


# 회원가입 API (모든 정보 DB 저장 및 비밀번호 암호화)
@app.route('/signup', methods=['POST'])
def signup():
    id_receive = request.form.get('id')
    name_receive = request.form.get('name')
    sel1_receive = request.form.get('sel1')     # 정글랩
    sel2_receive = request.form.get('sel2')     # 기수
    number_receive = request.form.get('number') # 번호
    pw_receive = request.form.get('pw')

    # 서버 측 2차 중복 체크 (안전성 강화)
    if db.users.find_one({'id': id_receive}):
        return jsonify({'result': 'fail', 'msg': '이미 존재하는 ID입니다.'})

    # 5. 비밀번호 해시(Hash) 암호화
    hashed_password = bcrypt.hashpw(pw_receive.encode('utf-8'), bcrypt.gensalt())

    # 4. 아이디를 포함한 모든 정보 DB에 저장
    doc = {
        'id': id_receive,
        'name': name_receive,
        'lab': sel1_receive,
        'gisu': sel2_receive,
        'number': number_receive,
        'password': hashed_password.decode('utf-8')  # 해시된 비밀번호 문자열 저장
    }
    
    db.users.insert_one(doc)

    return jsonify({'result': 'success'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=3000, debug=True)