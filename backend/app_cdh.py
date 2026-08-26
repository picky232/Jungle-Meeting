from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv # dotenv 라이브러리 불러오기
# CA(인증기관) 루트 인증서 묶음 들고있는 패키지
import certifi
import json
import uuid
import markdown

import jwt
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from flask import make_response, redirect, url_for

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
    all_users = list(collection.find({}, {"_id": 0}))
    print(all_users)
    return render_template('main.html')

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

# 임시 코드
def demo_create_cookie(user):
    token = create_token(user)

    response = jsonify({'result': 'success'})

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        max_age=60*60*5
    )

    return response

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

        user = collection.find_one({'_id':mongo_id})

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
        return render_template('main.html')

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

@app.route('/checkId/<user_id>/<new_id>', methods=['GET'])
def checkId(user_id, new_id):

    if user_id == new_id:
        return jsonify({'result': 'success'})

    result = collection.find_one({"userId":new_id})

    if new_id == 'admin' or result is not None:
        return jsonify({'result': 'fail'})

    return jsonify({'result': 'success'})

# 나의회원정보 확인
@app.route('/description/<user_id>', methods=['GET'])
def descriptionPage(user_id):

    currentUser = get_current_user()

    if currentUser is None:
        return jsonify({'result': 'fail'})

    result = collection.find_one({"userId":user_id})

    if result is None:
        return jsonify({'result': 'fail'})
    
    if currentUser["_id"] != result["_id"]:
        return jsonify({'result': 'fail'})

    desc_html=markdown.markdown(result['desc']);
    
    return render_template(
        'Description.html',
        name=result['name'],
        userId=result['userId'],
        imgPath=result['imgPath'],
        lab=result['lab'],
        gen=result['gen'],
        num=result['num'],
        desc=desc_html,
        tags=result['tags']
        )

# 회원정보수정
@app.route('/userInfoPatch/<user_id>', methods=['PATCH'])
def userInfoPatch(user_id):
    result = collection.find_one({"userId":user_id})

    if result is None:
        return jsonify({'result': 'faile'})

    name = request.form.get('name')
    id = request.form.get('id')
    lab = request.form.get('lab')
    gen = request.form.get('gen')
    num = request.form.get('num')
    desc = request.form.get('desc')
    tags = request.form.get('tags', '[]')
    tags = json.loads(tags)
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
    {'_id': result['_id']},
    {
        "$set": updateData
    })

    return jsonify({ 'result': 'success' })

#회원정보수정페이지
@app.route('/fix-description/<user_id>', methods=['GET'])
def fixDescriptionPage(user_id):

    result = collection.find_one({"userId":user_id})
    tagResult = [
        tag['name']
        for tag in tagdb.find({}, {'_id':0,'name':1})
    ]

    if result is None:
        return render_template('main.html')
    
    return render_template(
        'FixDescription.html',
        name=result['name'],
        userId=result['userId'],
        imgPath=result['imgPath'],
        lab=result['lab'],
        gen=result['gen'],
        num=result['num'],
        desc=result['desc'],
        tags=result['tags'],
        dbTags=tagResult
        )

if __name__ == '__main__':
    app.run(debug=True, port=3000)
