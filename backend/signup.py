from flask import Flask, render_template, request, jsonify, redirect, url_for  	# Flask 웹 프레임워크와 필요한 모듈 불러오기
from pymongo import MongoClient			# MongoDB 연결을 위한 모듈
import bcrypt  	# 비밀번호 해시 암호화를 위한 라이브러리
									
app = Flask(__name__, template_folder="front/templates")  # Flask 애플리케이션 객체 생성

# MongoDB 클러스터 연결
client = MongoClient('mongodb://name:password@localhost:27017/')
db = client["JM"]
collection = db["users"]

# 화면 전환 라우트
@app.route('/signup', methods=['GET'])  # 회원가입 페이지 요청(GET)
def signup_page():
    return render_template('signup.html')  # signup.html 템플릿 반환

@app.route('/login', methods=['GET'])  # 로그인 페이지 요청(GET)
def login_page():
    return render_template('login.html')  # login.html 템플릿 반환


# 1. 아이디 중복 여부 확인 API
@app.route('/checkUserid', methods=['POST'])  # 아이디 중복 확인 요청(POST)
def check_userid():
    input_id = request.form.get('give_id')  # 클라이언트에서 전달된 아이디 값 받기
    
    # DB에서 해당 ID 탐색
    user = db.users.find_one({'id': input_id})  # users 컬렉션에서 id가 일치하는 문서 검색
    
    if user:
        # 2. 중복인 경우
        return jsonify({'exists': True})  # JSON 응답으로 중복 여부 True 반환
    else:
        # 3. 중복이 아닌 경우
        return jsonify({'exists': False})  # JSON 응답으로 중복 여부 False 반환


# 회원가입 API (모든 정보 DB 저장 및 비밀번호 암호화)
@app.route('/signup', methods=['POST'])  # 회원가입 요청(POST)
def signup():
    id_receive = request.form.get('id')        # 입력받은 아이디
    name_receive = request.form.get('name')    # 입력받은 이름
    sel1_receive = request.form.get('sel1')    # 선택한 정글랩
    sel2_receive = request.form.get('sel2')    # 선택한 기수
    number_receive = request.form.get('number')# 입력받은 번호
    pw_receive = request.form.get('pw')        # 입력받은 비밀번호

    # 서버 측 2차 중복 체크 (안전성 강화)
    if db.users.find_one({'id': id_receive}):  # DB에 동일 아이디 존재 여부 확인
        return jsonify({'result': 'fail', 'msg': '이미 존재하는 ID입니다.'})  # 중복이면 실패 응답

    # 5. 비밀번호 해시(Hash) 암호화
    hashed_password = bcrypt.hashpw(pw_receive.encode('utf-8'), bcrypt.gensalt()) 

    # 4. 아이디를 포함한 모든 정보 DB에 저장
    doc = {
        'id': id_receive,
        'name': name_receive,
        'lab': sel1_receive,
        'gisu': sel2_receive,
        'number': number_receive,
        'password': hashed_password  # 그대로 바이트로 저장
    }
    
    db.users.insert_one(doc)  # users 컬렉션에 문서 삽입

    return jsonify({'result': 'success'})  # 성공 응답 반환

if __name__ == '__main__':  # 프로그램 실행 진입점
    app.run('0.0.0.0', port=5000, debug=True)  # Flask 서버 실행 (모든 IP에서 접근 가능, 포트 5000, 디버그 모드 활성화)
