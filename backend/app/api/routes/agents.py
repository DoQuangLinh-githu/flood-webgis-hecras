# backend/app/api/routes/agents.py

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.agent import Agent

router = APIRouter()


@router.post("/agents/heartbeat")
async def agent_heartbeat(
    request: Request,
    heartbeat: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Receive agent heartbeat"""
    # Get headers from request
    headers = request.headers
    agent_name = headers.get("x-agent-name")
    agent_token = headers.get("x-agent-token")
    
    print("=" * 60)
    print("📨 HEARTBEAT RECEIVED")
    print("=" * 60)
    print(f"All Headers: {dict(headers)}")
    print(f"X-Agent-Name: {agent_name}")
    print(f"X-Agent-Token: {agent_token}")
    print(f"Body: {heartbeat}")
    print("=" * 60)
    
    if not agent_name or not agent_token:
        print("❌ Missing headers!")
        raise HTTPException(status_code=401, detail="Missing authentication headers")

    if agent_token != "your-agent-secret-token-change-in-production":
        print("❌ Invalid token!")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Tìm hoặc tạo agent
    agent = db.query(Agent).filter(Agent.agent_name == agent_name).first()

    if not agent:
        agent = Agent(
            agent_name=agent_name,
            machine_name=heartbeat.get("machine_name", agent_name),
            status=heartbeat.get("status", "ONLINE"),
            version=heartbeat.get("version", "1.0.0"),
            last_seen=datetime.now()
        )
        db.add(agent)
        print(f"✅ New agent registered: {agent_name}")
    else:
        agent.status = heartbeat.get("status", "ONLINE")
        agent.last_seen = datetime.now()
        print(f"✅ Agent updated: {agent_name}")

    db.commit()
    return {"status": "ok"}