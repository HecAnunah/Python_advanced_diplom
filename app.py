from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder="dist", template_folder="dist")


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


# Тестовые данные пользователя
@app.route("/api/users/me")
def get_me():
    return jsonify(
        {
            "id": 1,
            "username": "zakhar",
            "email": "zakhar@example.com",
            "name": "Zakhar",
            "bio": "Backend developer",
            "avatar": "/favicon.ico",
            "is_active": True,
            "is_superuser": False,
            "api_key": "1",
        }
    )


# Тестовые посты
@app.route("/api/posts")
def get_posts():
    return jsonify(
        [
            {"id": 1, "author": "Zakhar", "content": "Hello, Twitter!", "likes": 3},
            {"id": 2, "author": "Alice", "content": "Good morning ☀️", "likes": 5},
        ]
    )


# Тестовый вход
@app.route("/api/auth/login", methods=["POST"])
def login():
    return jsonify({"access_token": "fake-token-123"})


if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    app.run(debug=True)
