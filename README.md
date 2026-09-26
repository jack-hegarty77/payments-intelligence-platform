## Start the app

From the repository root:

```sh
./start.sh
```

This starts the frontend at http://127.0.0.1:5173/ and the backend at
http://127.0.0.1:8000/. Press Ctrl+C to stop both servers.

The launcher expects `backend/venv` and `frontend/node_modules` to already
exist. To install them:

```sh
python3 -m venv backend/venv
backend/venv/bin/python -m pip install fastapi uvicorn
npm --prefix frontend install
```
