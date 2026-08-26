from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
import certifi
import boto3
import bcrypt
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
if not mongo_uri:
    raise ValueError("MONGO_URI가 설정되어 있지 않습니다.")

# 인증서 파일 경로 문자열 리턴
ca = certifi.where()

# MongoDB 클러스터 연결
client = MongoClient(mongo_uri, tlsCAFile=ca) # 인증서 검증시 ca에 담아둔 경로 사용
db = client["JM"]
collection = db["users"]

# 화면 전환 라우트
@app.route('/signup', methods=['GET']) 
def signup_page():  # 회원가입 페이지
    return render_template('signup.html') 

@app.route('/login', methods=['GET']) 
def login_page():  # 로그인 페이지
    return render_template('login.html') 

#메인페이지
@app.route('/main/<user_id>')
def mainpage(user_id):
    all_users = list(collection.find({}, {"_id": 0}))
    return render_template(
        'main.html',
        userId=user_id
    )


# 아이디 중복 확인 API
@app.route('/checkUserid', methods=['POST'])
def check_userid():

    # form 데이터 또는 JSON 데이터 받기
    input_id = request.form.get('give_id')

    print("입력된 ID:", input_id)
    if not input_id:
        data = request.get_json(silent=True)
        if data:
            input_id = data.get('give_id')

    if not input_id:
        return jsonify({
            'exists': False,
            'result': 'fail',
            'msg': '아이디를 입력해주세요.'
        })

    # DB에서 아이디 확인
    user = collection.find_one({'userId': input_id})

    if user:
        return jsonify({
            'exists': True,
            'result': 'fail',
            'msg': '이미 존재하는 아이디입니다.'
        })

    return jsonify({
        'exists': False,
        'result': 'success',
        'msg': '사용 가능한 아이디입니다.'
    })


# 회원가입 API
@app.route('/signup', methods=['POST']) 
def signup(): 

    id_receive = request.form.get('id') 
    name_receive = request.form.get('name')  
    sel1_receive = request.form.get('sel1')  
    sel2_receive = request.form.get('sel2') 
    number_receive = request.form.get('number') 
    pw_receive = request.form.get('pw')

    if not id_receive: 
        return jsonify({ 
            'result': 'fail', 
            'msg': '아이디를 입력해주세요.'
        })

    if not pw_receive:
        return jsonify({ 
            'result': 'fail', 
            'msg': '비밀번호를 입력해주세요.' 
        })


    # 서버 측 2차 아이디 중복 확인
    existing_user = collection.find_one({'userId': id_receive}) 

    if existing_user:  # 같은 ID O
        return jsonify({ 
            'result': 'fail', 
            'msg': '이미 존재하는 ID입니다.' 
        })

    # 비밀번호 암호화
    hashed_password = bcrypt.hashpw(  # 해시 
        pw_receive.encode('utf-8'), 
        bcrypt.gensalt()  
    )

    # 회원 정보 생성
    doc = {  
        'userId': id_receive,  
        'name': name_receive, 
        'imgPath': '',  
        'lab': sel1_receive, 
        'gen': sel2_receive, 
        'num': number_receive, 
        'desc': '', 
        'tags': [], 
        'password': hashed_password  
    }

    collection.insert_one(doc)

    return jsonify({ 
        'result': 'success', 
        'msg': '회원가입이 완료되었습니다.' 
    })


# 로그인 처리
@app.route("/login", methods=["POST"])
def login():

    # JSON 데이터 받기
    data = request.get_json()

    # JSON 데이터가 없는 경우
    if not data:
        return jsonify({
            "success": False,
            "msg": "로그인 정보를 받을 수 없습니다."
        }), 400

    # ID / PW 받기
    input_id = data.get("give_id")
    input_pw = data.get("give_pw")

    # 앞뒤 공백 제거
    if input_id:
        input_id = input_id.strip()
    if input_pw:
        input_pw = input_pw.strip()

    # 입력값 확인
    if not input_id:
        return jsonify({
            "success": False,
            "msg": "ID를 입력해주세요."
        })

    if not input_pw:
        return jsonify({
            "success": False,
            "msg": "PW를 입력해주세요."
        })

    user = collection.find_one({"userId": input_id})

    if user is None:
        return jsonify({
            "result": "fail",
        })

    # DB에 저장된 비밀번호 가져오기
    hashed_password = user.get("password")

    if not hashed_password:
        return jsonify({
            "success": False,
            "msg": "등록된 비밀번호 정보를 찾을 수 없습니다."
        })


    # 비밀번호 확인
    try:
        password_match = bcrypt.checkpw(
            input_pw.encode("utf-8"),
            hashed_password
        )

    except Exception as e:
        print("비밀번호 확인 오류:", e)

        return jsonify({
            "success": False,
            "msg": "비밀번호 확인 중 오류가 발생했습니다."
        }), 500


    # 로그인 성공
    if password_match:

        print(f"로그인 성공: {input_id}")

        return jsonify({
            "success": True,
            "msg": "로그인 성공",
            "userId": user["userId"],
            "name": user.get("name", "")
        })


    # 로그인 실패
    print(f"로그인 실패: {input_id}")

    return jsonify({
        "success": False,
        "msg": "ID 또는 PW가 올바르지 않습니다."
    })

# 서버 실행
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )