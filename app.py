import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

from utils.youtube_service import search_videos, get_video_comments
from utils.sentiment_service import analyze_sentiments, get_active_model_name, get_available_model_names

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    videos = []

    if query:
        try:
            videos = search_videos(query=query, max_results=9)
        except Exception as exc:
            flash(f"Failed to search YouTube videos: {exc}", "danger")

    return render_template(
        "index.html",
        query=query,
        videos=videos,
    )


@app.route("/analyze/<video_id>", methods=["GET", "POST"])
def analyze(video_id):
    max_comments = int(request.form.get("max_comments", request.args.get("max_comments", 50)))
    requested_model_name = request.form.get("model_name", request.args.get("model_name", "")).strip() or None
    available_models = get_available_model_names()
    active_model_name = get_active_model_name(requested_model_name)

    try:
        comments = get_video_comments(video_id=video_id, max_results=max_comments)
    except Exception as exc:
        flash(f"Failed to fetch comments: {exc}", "danger")
        return redirect(url_for("index"))

    if not comments:
        flash("No comments found for this video, or comments are disabled.", "warning")
        return render_template(
            "analyze.html",
            video_id=video_id,
            max_comments=max_comments,
            comments=[],
            model_name=active_model_name,
            available_models=available_models,
            summary={"positive": 0, "negative": 0, "total": 0},
        )

    results, summary = analyze_sentiments(comments, model_name=active_model_name)

    return render_template(
        "analyze.html",
        video_id=video_id,
        max_comments=max_comments,
        comments=results,
        model_name=active_model_name,
        available_models=available_models,
        summary=summary,
    )


if __name__ == "__main__":
    app.run(debug=True)
