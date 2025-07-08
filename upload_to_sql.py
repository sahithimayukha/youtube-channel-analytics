import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------------------DB Setup------------------
conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={os.getenv("SQL_SERVER")};'
    f'DATABASE={os.getenv("SQL_DATABASE")};'
    f'UID={os.getenv("SQL_USERNAME")};'
    f'PWD={os.getenv("SQL_PASSWORD")}'
)


cursor = conn.cursor()

# ============ Upload youtube_videos ============
df = pd.read_csv('youtube_channel_data.csv', encoding='utf-8-sig')
df['publishedAt'] = pd.to_datetime(df['publishedAt'], format='%d-%m-%y')

df['duration_sec'] = df['duration_sec'].fillna(0).astype(float)
df['ctr'] = df['ctr'].fillna(0).astype(float)
df['engagement_rate'] = df['engagement_rate'].fillna(0).astype(float)
df['subscriber_gain'] = df['subscriber_gain'].fillna(0).astype(float)

for _, row in df.iterrows():
    duration = float(row.duration_sec or 0)
    ctr = float(row.ctr or 0)
    engagement = float(row.engagement_rate or 0)
    sub_gain = float(row.subscriber_gain or 0)
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM youtube_videos WHERE video_id = ?)
        INSERT INTO youtube_videos (video_id, title, publishedAt, views, likes, comments, duration_sec, video_type, ctr, engagement_rate, subscriber_gain)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row.video_id, row.video_id, row.title, row.publishedAt, row.views, row.likes, row.comments,
         row.duration_sec, row.video_type, row.ctr, row.engagement_rate, row.subscriber_gain)

# ============ Upload daily_subscribers ============
sub_df = pd.read_csv('daily_subscribers.csv', encoding='utf-8-sig')
sub_df['date'] = pd.to_datetime(sub_df['date'], format='%d-%m-%y')

for _, row in sub_df.iterrows():
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM daily_subscribers WHERE date = ?)
        INSERT INTO daily_subscribers (date, subscriber_count)
        VALUES (?, ?)
    """, row.date.date(), row.date.date(), row.subscriber_count)

# ============ Upload upload_schedule ============
schedule_df = pd.read_csv('upload_schedule.csv', encoding='utf-8-sig')

for _, row in schedule_df.iterrows():
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM video_upload_schedule WHERE video_id = ?)
        INSERT INTO video_upload_schedule (video_id, day_of_week, hour)
        VALUES (?, ?, ?)
    """, row.video_id, row.video_id, row.day_of_week, row.hour)

conn.commit()
cursor.close()
conn.close()
print("✅ All data uploaded to Azure SQL.")
