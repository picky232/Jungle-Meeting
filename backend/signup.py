# 1. 아이디 중복 버튼 클릭 시 아이디 중복 여부 확인
#   2. 중복이면 아이디 중복 경고문
#   3. 중복이 아니면 회원가입 가능
# 4. 아이디를 포함한 모든 정보 DB에 저장
#   5. 보안을 위해 비밀번호를 해시(Hash) 형태로 암호화합니다
# 6. 회원가입 버튼 클릭 시 로그인 페이지로 이동

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)

# MongoDB 연결 설정 
client = MongoClient('mongodb://localhost:5000/') #임시링크 
db = client.jungle_meeting

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
    app.run('0.0.0.0', port=5000, debug=True)