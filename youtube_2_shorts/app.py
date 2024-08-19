import datetime
import json
import os
import subprocess
from flask import Flask, request, jsonify, send_file
import openai
import yt_dlp
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)
load_dotenv()

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def download_video_from_url(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(UPLOAD_FOLDER, 'video.%(ext)s'),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=False)
            video_path = ydl.prepare_filename(info_dict)
            print(f"Video downloaded: {video_path}")
            return video_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        raise

def transcribe_audio_from_video(video_path):
    audio_file = "audio.mp3"
    try:
        subprocess.run(["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_file], check=True)
        print(f"Audio extracted: {audio_file}")

        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
            print("Transcription completed successfully")
            print(f"Transcript object: {transcript}")
            print(f"Type of transcript: {type(transcript)}")

            return transcript.text if hasattr(transcript, 'text') else transcript['text']

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        raise
    except Exception as e:
        print(f"Transcription error: {e}")
        raise

def analyze_transcript_for_summary(transcript):
    final_prompt = (
        "Analyze the following transcript and identify the most engaging and relevant parts for a 1-minute TikTok video."
        "The total duration of the selected segments should be 1 minute."
        " Please return the start and end times of these key segments in JSON format with the following structure:\n"
        "["
        "  {"
        "    \"title\": \"Segment Title\",\n"
        "    \"start_time\": \"HH:MM:SS\",\n"
        "    \"end_time\": \"HH:MM:SS\",\n"
        "    \"content\": \"short description of the content within this segment.\"\n"
        "  }"
        "]"
        f"Transcript:\n{transcript}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.7
        )
        message_content = response.choices[0].message.content.strip()

        print(f"Raw message content received: {message_content}")

        if message_content.startswith("```json") and message_content.endswith("```"):
            message_content = message_content[7:-3].strip()
        
        try:
            segments_json = json.loads(message_content)
            print("Converted JSON segments:", segments_json)
            return segments_json
        except json.JSONDecodeError:
            print("Error decoding JSON, attempting to fix the format.")

            fixed_content = message_content.replace("\n", "")
            segments_json = json.loads(fixed_content)
            return segments_json

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise
    except Exception as e:
        print(f"Error analyzing transcript: {e}")
        raise

def convert_time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def create_summary_video(video_path, segments):
    try:
        clips = []
        video_clip = VideoFileClip(video_path)

        for segment in segments:
            start_seconds = convert_time_to_seconds(segment['start_time'])
            end_seconds = convert_time_to_seconds(segment['end_time'])

            clip = video_clip.subclip(start_seconds, end_seconds)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips)
        summary_video_path = "summary_video.mp4"
        final_clip.write_videofile(summary_video_path)
        print(f"Summary video created: {summary_video_path}")

        return summary_video_path

    except Exception as e:
        print(f"Error creating summary video: {e}")
        raise

@app.route('/summarize_video', methods=['POST'])
def summarize_video():
    try:
        if 'video' in request.files:
            video_file = request.files['video']
            video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
            video_file.save(video_path)
            print(f"Video file saved: {video_path}")
        elif 'url' in request.form:
            video_url = request.form['url']
            video_path = download_video_from_url(video_url)
        else:
            return jsonify({'error': 'No video or URL provided'}), 400

        # get video duration
        video_clip = VideoFileClip(video_path)
        video_duration = video_clip.duration
        print(f"Video duration: {video_duration} seconds")

        transcript = transcribe_audio_from_video(video_path)
        segments = analyze_transcript_for_summary(transcript)

        if not segments:
            return jsonify({'error': 'No summary segments identified'}), 500
        
        summary_video_path = create_summary_video(video_path, segments)

        return send_file(summary_video_path, as_attachment=True)

    except Exception as e:
        print(f"Error in summarize_video route: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
