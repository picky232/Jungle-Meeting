from flask import Flask, render_template, jsonify, request

app = Flask( 
    # front폴더로 나누어서 Flask에서 templates, static을 찾게되면 backend/templates 등으로 찾게되서 경로 오류 발생함
    __name__, 
    template_folder="../front/templates",
    static_folder="../front/static"
)

# 시작 메인 페이지
@app.route('/')
def mainpage():
    return render_template('main.html')

# 프로필확인 페이지 - 사용자 -> 다른사용자 프로필 확인
@app.route('/profile', methods=['GET'])
def profilePage():
    return render_template('')

@app.route('/checkId/<user_id>', methods=['GET'])
def checkId(userId):
    if userId == 'admin':
        return jsonify({'result': 'fail'})

    return jsonify({'result': 'success'})

# 나의회원정보 확인
@app.route('/description', methods=['GET'])
def descriptionPage():
    return render_template('Description.html')

@app.route('/userInfoPatch', methods=['PATCH'])
def userInfoPatch():
    data = request.get_json()

    name = data['name']
    id = data['id']
    lab = data['lab']
    gen = data['gen']
    num = data['num']
    tags = data['tags']

@app.route('/fix-description', methods=['GET'])
def fixDescriptionPage():
    return render_template('FixDescription.html')

# 회원정보수정
@app.route('/rewriteProfile', methods=['POST'])
def reWrite():
    return render_template('')


if __name__ == '__main__':
    app.run(debug=True, port=3000)
