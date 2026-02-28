import sys
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", message=".*OpenSSL.*")

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import redirect_stdout
import io
import threading
import queue

from stages.stage1_topic import stage1_topic_decomposition
from stages.stage2_discovery import stage2_document_discovery
from stages.stage3_analysis import stage3_document_analysis
from stages.stage3b_deepen import stage3b_deepen_research
from stages.stage4_scoring import stage4_academic_scoring
from stages.stage5_filtering import stage5_selection_filtering
from stages.stage6_synthesis import stage6_research_synthesis
from stages.stage7_generation import stage7_paper_generation
from stages.stage8_review import stage8_review_paper
from utils.plagiarism_detector import analyze_plagiarism_and_novelty

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global queue for logs
log_queue = queue.Queue()

class OutputCapture(io.StringIO):
    def __init__(self, target_queue):
        super().__init__()
        self.target_queue = target_queue

    def write(self, text):
       
        sys.__stdout__.write(text)
        # Put in queue for WebSocket
        if text.strip(): # Avoid sending pure whitespace noise if possible, but keeping structure is mostly good
            self.target_queue.put(text)
        super().write(text)

    def flush(self):
        sys.__stdout__.flush()
        super().flush()

# --- Database Setup ---
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./research_history.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ResearchPaper(Base):
    __tablename__ = "research_papers"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Pipeline ---

# --- Auth System Setup ---
from jose import jwt
from pydantic import BaseModel
import bcrypt

SECRET_KEY = "supersecretkey" # In prod, use env var
ALGORITHM = "HS256"

AUTH_DB_URL = "sqlite:///./users.db"
AuthBase = declarative_base()
auth_engine = create_engine(AUTH_DB_URL, connect_args={"check_same_thread": False})
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

class User(AuthBase):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class OTP(AuthBase):
    __tablename__ = "otps"
    email = Column(String, primary_key=True, index=True)
    code = Column(String)
    expires_at = Column(DateTime)

AuthBase.metadata.create_all(bind=auth_engine)

class UserCreate(BaseModel):
    email: str
    password: str
    otp: str # Added OTP field

class UserLogin(BaseModel):
    email: str
    password: str

class OTPRequest(BaseModel):
    email: str

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

import random
from datetime import timedelta

@app.post("/send-otp")
def send_otp(req: OTPRequest):
    db = AuthSessionLocal()
    try:
        # Check if user already exists
        if db.query(User).filter(User.email == req.email).first():
            return {"error": "Email already registered"}

        # Generate OTP
        code = f"{random.randint(100000, 999999)}"
        expires = datetime.utcnow() + timedelta(minutes=10)
        
        # Upsert OTP
        otp_entry = db.query(OTP).filter(OTP.email == req.email).first()
        if otp_entry:
            otp_entry.code = code
            otp_entry.expires_at = expires
        else:
            otp_entry = OTP(email=req.email, code=code, expires_at=expires)
            db.add(otp_entry)
        
        db.commit()
        
        # SIMULATION: Print to console
        print(f"\n[OTP SERVICE] >>> Code for {req.email}: {code} <<<\n")
        
        return {"message": "OTP sent! (Check server console for code)"}
    finally:
        db.close()

@app.post("/register")
def register(user: UserCreate):
    db = AuthSessionLocal()
    try:
        # Verify OTP (unless Google Bypass)
        if user.otp != "GOOGLE_BYPASS":
            otp_entry = db.query(OTP).filter(OTP.email == user.email).first()
            if not otp_entry or otp_entry.code != user.otp:
                return {"error": "Invalid OTP code"}
            
            if otp_entry.expires_at < datetime.utcnow():
                return {"error": "OTP expired"}
            
            # Clean up OTP
            db.delete(otp_entry)

        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            return {"error": "Email already registered"}
        
        hashed = get_password_hash(user.password)
        new_user = User(email=user.email, hashed_password=hashed)
        db.add(new_user)
        
        db.commit()
        return {"message": "User registered successfully"}
    finally:
        db.close()

@app.post("/login")
def login(user: UserLogin):
    db = AuthSessionLocal()
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            return {"error": "Invalid credentials"}
        
        token = create_access_token({"sub": db_user.email})
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()

class PlagiarismRequest(BaseModel):
    text: str

@app.post("/api/plagiarism/analyze")
def manually_analyze_plagiarism(req: PlagiarismRequest):
    try:
        # Generic endpoint for Plagiarism dashboard UI
        result = analyze_plagiarism_and_novelty(req.text)
        return result
    except Exception as e:
        return {"error": str(e)}

import tempfile
import os
from groq import Groq

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            return {"error": "Groq API key not configured on backend."}
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(await file.read())
            temp_path = temp_audio.name
            
        try:
            client = Groq(api_key=groq_api_key)
            with open(temp_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                  file=(file.filename, f.read()),
                  model="whisper-large-v3-turbo",
                )
            return {"transcript": transcription.text}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Transcription failed: {str(e)}"}

# --- Main Pipeline ---

import hashlib
import json
import os

CACHE_DIR = "./memory_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_cache_path(topic, stage_name):
    topic_hash = hashlib.md5(topic.strip().lower().encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{topic_hash}_{stage_name}.json")

def load_stage_cache(topic, stage_name):
    path = _get_cache_path(topic, stage_name)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_stage_cache(topic, stage_name, data):
    path = _get_cache_path(topic, stage_name)
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to cache {stage_name}: {e}")

def save_research_to_db(topic, content):
    db = SessionLocal()
    try:
        paper = ResearchPaper(topic=topic, content=content)
        db.add(paper)
        db.commit()
        db.refresh(paper)
        print(f"Saved research on '{topic}' to DB (ID: {paper.id})")
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        db.close()

def run_research_pipeline(topic, log_queue):
    try:
        sys.__stdout__.write(f"DEBUG: run_research_pipeline called for {topic}\n")
        capture = OutputCapture(log_queue)
        from contextlib import redirect_stderr
        with redirect_stdout(capture), redirect_stderr(capture):
            sys.__stdout__.write("DEBUG: Inside redirect block\n")
            try:
                # ... (Pipeline Stages 1-8 same as before)
                # COPIED EXISTING LOGIC SHORTHAND FOR BREVITY IN EDIT
                print(f"Starting research on: {topic}")
                
                log_queue.put("STAGE:1") 
                decomposition = load_stage_cache(topic, "stage1")
                if not decomposition:
                    decomposition = stage1_topic_decomposition(topic)
                    if not decomposition: 
                        log_queue.put("ERROR: Stage 1 Topic Decomposition failed natively (Returned None). Verify LLM API quotas.")
                        return
                    save_stage_cache(topic, "stage1", decomposition)
                else:
                    print(f"  [Memory] Restored Stage 1: Topic Decomposition from cache.")

                log_queue.put("STAGE:2")
                raw_docs = load_stage_cache(topic, "stage2")
                if not raw_docs:
                    raw_docs = stage2_document_discovery(decomposition)
                    save_stage_cache(topic, "stage2", raw_docs)
                else:
                    print(f"  [Memory] Restored Stage 2: Document Discovery from cache.")
                
                log_queue.put("STAGE:3")
                analyzed_docs = load_stage_cache(topic, "stage3")
                if not analyzed_docs:
                    analyzed_docs = stage3_document_analysis(raw_docs or []) # Empty list fallback for robust flow
                    save_stage_cache(topic, "stage3", analyzed_docs)
                else:
                    print(f"  [Memory] Restored Stage 3: Document Analysis from cache.")

                log_queue.put("STAGE:3b")
                # Bypass Deepen stage cache since it relies on modifying analyzing docs, run it dynamically
                deep_docs = stage3b_deepen_research(analyzed_docs, topic)
                if deep_docs: analyzed_docs.extend(deep_docs)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                log_queue.put(f"ERROR: Fatal Pipeline Crash: {str(e)}\n\nTraceback: {error_trace}")
                return

            log_queue.put("STAGE:4")
            scored_docs = load_stage_cache(topic, "stage4")
            if not scored_docs:
                scored_docs = stage4_academic_scoring(analyzed_docs, topic)
                save_stage_cache(topic, "stage4", scored_docs)
            else:
                print(f"  [Memory] Restored Stage 4: Academic Scoring from cache.")

            log_queue.put("STAGE:5")
            knowledge_base = load_stage_cache(topic, "stage5")
            if not knowledge_base:
                knowledge_base = stage5_selection_filtering(scored_docs)
                save_stage_cache(topic, "stage5", knowledge_base)
            else:
                print(f"  [Memory] Restored Stage 5: Selection Filtering from cache.")
                
            if not knowledge_base:
                log_queue.put("ERROR:No valid docs")
                return

            log_queue.put("STAGE:6")
            synthesis = load_stage_cache(topic, "stage6")
            if not synthesis:
                synthesis = stage6_research_synthesis(knowledge_base, topic)
                save_stage_cache(topic, "stage6", synthesis)
            else:
                print(f"  [Memory] Restored Stage 6: Research Synthesis from cache.")
            if not synthesis: return

            log_queue.put("STAGE:7")
            loop_count = 0
            max_loops = 3
            feedback = ""
            final_paper = ""

            while loop_count < max_loops:
                final_paper = stage7_paper_generation(synthesis, knowledge_base, topic, feedback=feedback)
                log_queue.put("STAGE:8")
                review = stage8_review_paper(final_paper, topic)
                if review.get('score', 0) >= 6: break
                feedback = review.get('critique', '')
                loop_count += 1
            
            # SAVE TO DB
            save_research_to_db(topic, final_paper)

            log_queue.put("COMPLETE")
            log_queue.put(f"FINAL_PAPER_CONTENT:{final_paper}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_queue.put(f"ERROR:{str(e)}")

# ... (WebSocket handler same as before)

@app.get("/history")
def get_history():
    db = SessionLocal()
    try:
        papers = db.query(ResearchPaper).order_by(ResearchPaper.created_at.desc()).all()
        return [{"id": p.id, "topic": p.topic, "date": p.created_at, "preview": p.content[:200]} for p in papers]
    finally:
        db.close()

@app.get("/history/{paper_id}")
def get_history_detail(paper_id: int):
    db = SessionLocal()
    try:
        p = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if p:
            return {"id": p.id, "topic": p.topic, "date": p.created_at, "content": p.content}
        return {"error": "Not found"}
    finally:
        db.close()

# ... (rest of main)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    try:
        while True:
            # Wait for instruction from client
            data = await websocket.receive_text()
            
            if data.startswith("START:"):
                topic = data[6:]
                sys.__stdout__.write(f"DEBUG: START command received for topic: {topic}\n")
                
     
                ws_log_queue = queue.Queue()
                
                # Run pipeline in a separate thread so we don't block the websocket loop
                t = threading.Thread(target=run_research_pipeline, args=(topic, ws_log_queue))
                t.start()
                sys.__stdout__.write(f"DEBUG: Thread started. ID: {t.ident}\n")
                
             
                while t.is_alive() or not ws_log_queue.empty():
                    try:
                        # Non-blocking get
                        msg = ws_log_queue.get(timeout=0.1)
                        if msg:
                             # sys.__stdout__.write(f"DEBUG: Sending WS message: {msg[:50]}...\n")
                             await websocket.send_text(msg)
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                        
                await websocket.send_text("DONE")
                sys.__stdout__.write("DEBUG: Pipeline finished (thread dead and queue empty).\n")
                
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
