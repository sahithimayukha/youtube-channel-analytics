import pandas as pd
import requests
from datetime import datetime
import isodate
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Get upload playlist ID
url_channel = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails,statistics&id={CHANNEL_ID}&key={API_KEY}"
response = requests.get(url_channel).json()
uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
subscriber_count = int(response['items'][0]['statistics']['subscriberCount'])

# Get all video Ids from playlist
video_id = []
next_page_token = None
while True:
    playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={uploads_playlist_id}&maxResults=50&pageToken={next_page_token or ''}&key={API_KEY}"
    playlist_response = requests.get(playlist_url).json()
    for item in playlist_response['items']:
        video_id.append(item['contentDetails']['videoId'])

    next_page_token = playlist_response.get('nextPageToken')
    if not next_page_token:
        break


# Get video statistics for each video
video_data = []
upload_schedule = []

for i in range(0, len(video_id), 50):
    ids = ','.join(video_id[i:i+50])
    stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={ids}&key={API_KEY}"
    stats_response = requests.get(stats_url).json()

    for video in stats_response['items']:
        snippet = video['snippet']
        stats = video['statistics']
        duration_iso = video['contentDetails']['duration']
        duration_sec = isodate.parse_duration(duration_iso).total_seconds()
        video_type = 'Shorts' if duration_sec < 60 else 'Video'

        published_at = pd.to_datetime(snippet['publishedAt'])
        day_of_week = published_at.strftime('%A')
        hour = published_at.hour

        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        engagement_rate = (likes + comments) / views if views > 0 else 0

        video_data.append({
            'video_id' : video['id'],
            'title' : snippet['title'],
            'publishedAt' : published_at,
            'views' : views,
            'likes' : likes,
            'comments': comments,
            'duration_sec' : duration_sec,
            'video_type' : video_type,
            'ctr' : None,
            'engagement_rate' : engagement_rate,
            'subscriber_gain' : None
        })

        upload_schedule.append({
            'video_id': video['id'],
            'day_of_week': day_of_week,
            'hour': hour
        })


# ============ Save Video Data ============
df = pd.DataFrame(video_data)
df['publishedAt'] = pd.to_datetime(df['publishedAt']).dt.strftime('%d-%m-%y')
df.to_csv('youtube_channel_data.csv', index=False, encoding='utf-8-sig')
print("youtube_channel_data.csv saved.")

# ============ Save Upload Schedule ============
schedule_df = pd.DataFrame(upload_schedule)
schedule_df.to_csv('upload_schedule.csv', index=False, encoding='utf-8-sig')
print("upload_schedule.csv saved.")

# ============ Save Daily Subscribers (no duplicates) ============
today = datetime.today().strftime('%d-%m-%y')
subscriber_data = {'date': today, 'subscriber_count': subscriber_count}
file_path = 'daily_subscribers.csv'

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    existing_df = pd.read_csv(file_path)
    existing_df['date'] = existing_df['date'].astype(str)
    if today not in existing_df['date'].tolist():
        updated_df = pd.concat([existing_df, pd.DataFrame([subscriber_data])])
        updated_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print("Subscriber data added.")
    else:
        print("Subscriber data for today already exists.")
else:
    pd.DataFrame([subscriber_data]).to_csv(file_path, index=False, encoding='utf-8-sig')
    print("New subscriber file created.")