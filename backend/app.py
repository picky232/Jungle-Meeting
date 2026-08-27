from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi

from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi

from bson import ObjectId
import json
import uuid
import markdown
import bcrypt
from flask import redirect, url_for
import jwt

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
jwt_secret = os.environ.get("JWT_SECRET")

# 인증서 파일 경로 문자열 리턴
ca = certifi.where()

# MongoDB 클러스터 연결
client = MongoClient(mongo_uri, tlsCAFile=ca) # 인증서 검증시 ca에 담아둔 경로 사용
db = client["JM"]
collection = db["users"]
tagdb = db["tags"]

# 시작 메인 페이지
@app.route('/')
def mainpage():
    return render_template('main.html')

@app.context_processor
def inject_user():
    currentUser = get_current_user()

    return {
        'userName':currentUser['name'] if currentUser is not None else None,
        'currentUser':currentUser,
        'isLoggedIn':currentUser is not None
    }


@app.route('/maketags', methods=['GET'])
def makeTag():
    tagData = list(tagdb.find({}, {"_id":0}))
    print(tagData)
    return jsonify(tagData)


@app.route('/makeCard/jungle', methods=['GET'])
def makeCard():
    currentUser = get_current_user()

    if currentUser is None:
        userData = list(collection.find({}, {
            "_id":0,
            "desc":0,
            "password":0
            }))
        
        return jsonify(userData)
        
    currentTags = set(currentUser.get("tags", []))

    userData = list(collection.find(
        {
        "_id":{
            "$ne":currentUser["_id"]
        }
        },
        {
            "_id":0,
            "desc":0,
            "password":0
        }))

    for user in userData:
        userTags = set(user.get("tags", []))

        user["sameTagCnt"] = len(
            currentTags & userTags
        )

    userData.sort(
        key=lambda user: user['sameTagCnt'],
        reverse=True
    )
        
    # 딕셔너리에서 password필드 제거
    return jsonify(userData)

################################################################

# user = collection.find_one({"userId": user_id})
def create_token(user):
    payload = {
        "sub": str(user['_id'])
    }

    return jwt.encode(
        payload,
        jwt_secret,
        algorithm="HS256"
    )

def get_current_user():
    token = request.cookies.get("access_token")

    if token is None:
        return None

    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"]
        )

        mongo_id = payload.get("sub")

        if mongo_id is None:
            return None

        user = collection.find_one({'_id':ObjectId(mongo_id)})

        return user
    except(
        jwt.ExpiredSignatureError, #쿠키 유효시간
        jwt.InvalidTokenError, #jwt가 이상할 떄 (변조, 가짜 등)
        ValueError #내부 밸류 오류
    ):
        return None

# 프로필확인 페이지 - 사용자 -> 다른사용자 프로필 확인
@app.route('/profile/<user_id>', methods=['GET'])
def profilePage(user_id):
    
    result = collection.find_one({"userId":user_id})

    if result is None:
        return redirect(url_for('mainpage'))

    desc_html=markdown.markdown(result['desc']);

    return render_template(
        'Profile.html',
        name=result['name'],
        userId=result['userId'],
        imgPath=result['imgPath'],
        lab=result['lab'],
        gen=result['gen'],
        num=result['num'],
        desc=desc_html,
        tags=result['tags']
        )

@app.route('/checkId/<new_id>', methods=['GET'])
def checkId(new_id):
    currentUser = get_current_user()

    if currentUser['userId'] == new_id:
        return jsonify({'result': 'success'})

    result = collection.find_one({"userId":new_id})

    if new_id == 'admin' or result is not None:
        return jsonify({'result': 'fail'})

    return jsonify({'result': 'success'})

# 나의회원정보 확인
@app.route('/description', methods=['GET'])
def descriptionPage():
    currentUser = get_current_user()

    if currentUser is None:
        return redirect(url_for('mainpage'))

    desc_html=markdown.markdown(currentUser['desc'])
    
    return render_template(
        'Description.html',
        name=currentUser['name'],
        userId=currentUser['userId'],
        imgPath=currentUser['imgPath'],
        lab=currentUser['lab'],
        gen=currentUser['gen'],
        num=currentUser['num'],
        desc=desc_html,
        tags=currentUser['tags']
        )

# 회원정보수정
@app.route('/userInfoPatch', methods=['PATCH'])
def userInfoPatch():
    currentUser = get_current_user()

    if currentUser is None:
        return jsonify({'result': 'fail'})
    
    id = request.form.get('id')

    if id != currentUser['userId']:
        duplicateUser = collection.find_one({id})
        if duplicateUser is not None:
            return jsonify({'result':'fail'})

    name = request.form.get('name')
    lab = request.form.get('lab')
    gen = request.form.get('gen')
    num = request.form.get('num')
    desc = request.form.get('desc')
    tags = request.form.get('tags', '[]')
    tags = json.loads(tags)
    tags=[
        ''.join(tag.split()).upper()
        for tag in tags
        if ''.join(tag.split())
    ]
    tags = list(dict.fromkeys(tags))

    tagdb.create_index('name', unique=True)

    for tag in tags:
        tagdb.update_one(
            {'name':tag},
            {'$setOnInsert': {'name':tag}}, #insert
            upsert=True #update할 문서 없으면 insert
        )

    updateData = {
        'name': name,
        'userId': id,
        'lab': lab,
        'gen': gen,
        'num': num,
        'desc': desc,
        'tags': tags
    }

    if 'profileImg' in request.files:
        file = request.files['profileImg']

        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"

            upload_folder_path = os.path.join(app.static_folder, 'images', 'profile')
            os.makedirs(upload_folder_path, exist_ok=True)
            save_path = os.path.join(upload_folder_path, filename)
            file.save(save_path) # 실제 저장 경로

            updateData['imgPath'] = f'/static/images/profile/{filename}' #브라우저가 들어갈 경로


    collection.update_one(
    {'_id': currentUser['_id']},
    {
        "$set": updateData
    })

    return jsonify({ 'result': 'success' })

#회원정보수정페이지
@app.route('/fix-description', methods=['GET'])
def fixDescriptionPage():
    currentUser = get_current_user()

    if currentUser is None:
        return redirect(url_for('mainpage'))
    
    tagResult = [
        tag['name']
        for tag in tagdb.find({}, {'_id':0,'name':1})
    ]

    return render_template(
        'FixDescription.html',
        name=currentUser['name'],
        userId=currentUser['userId'],
        imgPath=currentUser['imgPath'],
        lab=currentUser['lab'],
        gen=currentUser['gen'],
        num=currentUser['num'],
        desc=currentUser['desc'],
        tags=currentUser['tags'],
        dbTags=tagResult
        )


# 화면 전환 라우트
@app.route('/signup', methods=['GET']) 
def signup_page():  # 회원가입 페이지
    return render_template('signup.html') 

@app.route('/login', methods=['GET']) 
def login_page():  # 로그인 페이지
    return render_template('login.html') 

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

        token = create_token(user)

        response = jsonify({
            "success": True,
            "msg": "로그인 성공",
            "userId": user["userId"],
            "name": user.get("name", "")
        })

        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            max_age=60*60*5
        )
        return response

    # 로그인 실패
    print(f"로그인 실패: {input_id}")

    return jsonify({
        "success": False,
        "msg": "ID 또는 PW가 올바르지 않습니다."
    })

@app.route("/logout", methods=["GET"])
def logout():
    response = jsonify({
        'result': 'success'
    })

    response.delete_cookie('access_token')

    return response

@app.route("/delete", methods=["DELETE"])
def deleteUser():
    currentUser = get_current_user()

    if currentUser is None:
        return jsonify({'result':'fail'})

    collection.delete_one({"_id": currentUser["_id"]})

    return logout()
    
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=3000,
        debug=True
    )