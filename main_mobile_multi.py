from core.camera_manager import camera_manager
import uvicorn

if __name__ == "__main__":
    camera_manager.start()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)

