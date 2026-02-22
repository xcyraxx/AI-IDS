import multiprocessing
import uvicorn
import time
from core.sniffer import start_sniffing
from core.detector import detect_loop
from api import app

def run_sniffer():
    try:
        start_sniffing()
    except KeyboardInterrupt:
        pass

def run_detector():
    try:
        detect_loop()
    except KeyboardInterrupt:
        pass

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_frontend():
    import subprocess
    import os
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if os.path.exists(frontend_dir):
        print("🌐 Starting Frontend (Vite)...")
        # Run npm run dev inside the frontend directory
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
    else:
        print("⚠️ Frontend directory not found. Skipping...")

if __name__ == "__main__":
    print("🚀 Starting AI-IDS Integrated System...")
    
    # Create processes
    sniffer_proc = multiprocessing.Process(target=run_sniffer, name="Sniffer")
    detector_proc = multiprocessing.Process(target=run_detector, name="Detector")
    api_proc = multiprocessing.Process(target=run_api, name="API")
    frontend_proc = multiprocessing.Process(target=run_frontend, name="Frontend")

    try:
        sniffer_proc.start()
        detector_proc.start()
        api_proc.start()
        frontend_proc.start()

        print("✅ All components started.")
        print("   - API: http://localhost:8000")
        print("   - Frontend: Check console for Vite URL (usually http://localhost:5173)")
        
        while True:
            time.sleep(1)
            if not sniffer_proc.is_alive():
                print("⚠️ Sniffer process died. Restarting...")
                sniffer_proc = multiprocessing.Process(target=run_sniffer)
                sniffer_proc.start()
            if not detector_proc.is_alive():
                print("⚠️ Detector process died. Restarting...")
                detector_proc = multiprocessing.Process(target=run_detector)
                detector_proc.start()
            if not api_proc.is_alive():
                print("⚠️ API process died. Restarting...")
                api_proc = multiprocessing.Process(target=run_api)
                api_proc.start()
            if not frontend_proc.is_alive():
                print("⚠️ Frontend process died. Restarting...")
                frontend_proc = multiprocessing.Process(target=run_frontend)
                frontend_proc.start()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        sniffer_proc.terminate()
        detector_proc.terminate()
        api_proc.terminate()
        frontend_proc.terminate()
        sniffer_proc.join()
        detector_proc.join()
        api_proc.join()
        frontend_proc.join()
        print("👋 Done.")
