from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)



# Flask 실행
if __name__ == '__main__':
    app.run(debug=True, port=5000)



    # 1. 로그인 버튼 클릭 시 아이디를 기준으로 회원정보 조회
    #   2. 비번 일치 여부 확인
    #    3. 일치하면 아이디 비번정보로 로그인 (메인)
    #    4. 일치하지 않으면 회원가입하세요 경고문
    # 5. 인증에 성공하면 세션(Session) 객체에 회원 정보
    # 6. 서버가 세션 ID를 생성해 응답 쿠키(JSESSIONID 등)로 클라이언트에 전달
    # 7. 회원가입 버튼 클릭 시 회원가입 페이지로 이동