import os
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_CONTEXT = """
You are an enterprise AI Surveillance Intelligence Assistant for Sentinel AI.
You analyze surveillance data, alerts, camera feeds, and security incidents.
Always respond professionally, concisely, and in bullet points where helpful.
Format responses clearly for a security operations dashboard.
Current time: {time}
"""

MOCK_DATA = """
Today's data:
- Total cameras: 16 (12 active, 4 offline)
- Critical alerts: 12 (most from Warehouse Zone B)
- Peak activity: 8 PM to 10 PM
- Intrusion alerts: 3 (between 7 PM - 9 PM)
- Occupancy events: 14
- Most active camera: Camera 07 - Warehouse Zone B
- Suspicious movement detected near: Restricted Zone C
- Retail Zone traffic: 340 people (up 18% from yesterday)
- Threat level: Medium
"""


class ChatRequest(BaseModel):
    message: str


class IncidentRequest(BaseModel):
    zone: str
    start_time: str
    end_time: str


@app.post("/chat")
async def chat(req: ChatRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

Surveillance context:
{MOCK_DATA}

User question: {req.message}

Respond professionally. Use bullet points. Keep it under 120 words.
"""
    response = model.generate_content(prompt)
    return {"response": response.text}


@app.post("/incident-summary")
async def incident_summary(req: IncidentRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

Generate a professional incident summary report for:
Zone: {req.zone}
Time period: {req.start_time} to {req.end_time}

{MOCK_DATA}

Format as a structured incident report with:
- Overview
- Key events (bullet points)
- Risk assessment
- Recommended actions
Keep under 150 words.
"""
    response = model.generate_content(prompt)
    return {"summary": response.text}


@app.post("/analytics-query")
async def analytics_query(req: ChatRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

{MOCK_DATA}

Analytics question: {req.message}

Respond with specific data points, numbers, and trends.
Use bullet points. Under 100 words.
"""
    response = model.generate_content(prompt)
    return {"response": response.text}


@app.get("/health")
async def health():
    return {"status": "ok", "model": "gemini-1.5-flash"}
