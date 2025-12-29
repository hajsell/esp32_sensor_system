from flask import session

@app.route("/test-session")
def test_session():
    session["test"] = "ok"
    return "session set"
