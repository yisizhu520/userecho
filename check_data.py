import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import func, select, and_

# Add server directory to path so we can import backend modules
sys.path.append(os.path.join(os.getcwd(), 'server'))

from backend.database.db import async_db_session
from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.model.topic import Topic

async def check_data():
    async with async_db_session() as db:
        now = datetime.now()
        start_date = now - timedelta(days=now.weekday()) # Monday
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"Checking data since: {start_date}")
        
        # Check Feedbacks
        query_feedbacks = select(func.count(Feedback.id)).where(
            Feedback.submitted_at >= start_date
        )
        result = await db.execute(query_feedbacks)
        feedback_count = result.scalar()
        print(f"Feedbacks this week: {feedback_count}")

        # Check Topics
        query_topics = select(func.count(Topic.id)).where(
            Topic.created_time >= start_date
        )
        result = await db.execute(query_topics)
        topic_count = result.scalar()
        print(f"Topics this week: {topic_count}")
        
        # Check Total Feedbacks
        query_total = select(func.count(Feedback.id))
        result = await db.execute(query_total)
        total_feedback = result.scalar()
        print(f"Total Feedbacks (all time): {total_feedback}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_data())
