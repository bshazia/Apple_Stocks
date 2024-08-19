import datetime
import json
import os
import subprocess
from flask import Flask, request, jsonify, send_file
import openai
import yt_dlp
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, concatenate_videoclips,TextClip, CompositeVideoClip


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



# Function to extract audio from a video
def extract_audio_from_video(video_path):
    video = VideoFileClip(video_path)
    audio_path = video_path.rsplit('.', 1)[0] + ".mp3"
    video.audio.write_audiofile(audio_path)
    return audio_path


# Function to create subtitles as a TextClip
def create_subtitles(video, transcript):
    subtitle_clips = []
    words = transcript.split()
    duration_per_word = video.duration / len(words)

    for i, word in enumerate(words):
        txt_clip = TextClip(word, fontsize=24, color='white', size=video.size)
        txt_clip = txt_clip.set_duration(duration_per_word)
        txt_clip = txt_clip.set_start(i * duration_per_word)
        txt_clip = txt_clip.set_position(("center", "bottom"))
        subtitle_clips.append(txt_clip)

    return subtitle_clips

# Function to overlay subtitles onto the video
def add_subtitles_to_video(video_path, transcript):
    video = VideoFileClip(video_path)
    subtitles = create_subtitles(video, transcript)
    video_with_subtitles = CompositeVideoClip([video, *subtitles])
    output_path = video_path.rsplit('.', 1)[0] + "_with_subtitles.mp4"
    video_with_subtitles.write_videofile(output_path, codec="libx264", fps=24)
    return output_path

# Main function to process the video
def process_video_with_subtitles(video_path):
    # Extract audio from the video
    audio_path = extract_audio_from_video(video_path)
    
    # Transcribe the audio using OpenAI Whisper
    transcript = transcribe_audio_from_video(audio_path)
    
    # Add subtitles to the video
    video_with_subtitles_path = add_subtitles_to_video(video_path, transcript)
    
    return video_with_subtitles_path

@app.route('/summarize_video', methods=['POST'])
def short_video():
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

        # Get video duration
        video_clip = VideoFileClip(video_path)
        video_duration = video_clip.duration
        print(f"Video duration: {video_duration} seconds")

        # Transcribe audio and analyze transcript
        transcript = transcribe_audio_from_video(video_path)
        segments = analyze_transcript_for_summary(transcript)

        if not segments:
            return jsonify({'error': 'No summary segments identified'}), 500
        
        summary_video_path = create_summary_video(video_path, segments)
        #subtitls
        subittlesadd = process_video_with_subtitles(summary_video_path)
        # Return the summary video as a downloadable file
        return send_file(subittlesadd, as_attachment=True)

    except Exception as e:
        print(f"Error in summarize_video route: {e}")
        return jsonify({'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
