import uvicorn

if __name__ == "__main__":
    # FastAPIアプリケーションを起動
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 