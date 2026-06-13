import os
from googleapiclient.discovery import build


def get_youtube_client():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is missing. Add it to your .env file.")

    return build("youtube", "v3", developerKey=api_key)


def search_videos(query: str, max_results: int = 9):
    youtube = get_youtube_client()

    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results,
        order="relevance",
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        videos.append(
            {
                "video_id": item["id"]["videoId"],
                "title": snippet.get("title", "No title"),
                "channel": snippet.get("channelTitle", "Unknown channel"),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "published_at": snippet.get("publishedAt", ""),
            }
        )

    return videos


def get_video_comments(video_id: str, max_results: int = 50):
    youtube = get_youtube_client()

    comments = []
    next_page_token = None

    while len(comments) < max_results:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_results - len(comments)),
            textFormat="plainText",
            order="relevance",
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append(
                {
                    "author": top_comment.get("authorDisplayName", "Unknown"),
                    "author_image": top_comment.get("authorProfileImageUrl", ""),
                    "text": top_comment.get("textDisplay", ""),
                    "like_count": top_comment.get("likeCount", 0),
                    "published_at": top_comment.get("publishedAt", ""),
                }
            )

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments
