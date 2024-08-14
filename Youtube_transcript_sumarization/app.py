from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from dotenv import load_dotenv
import openai
import os

import yt_dlp




load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
app = Flask(__name__)


#download audio from YouTube video
def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        audio_file = ydl.prepare_filename(info_dict)
        audio_file = audio_file.rsplit('.', 1)[0] + ".mp3"
    
    return audio_file

#transcribe audio using OpenAI Whisper
def transcribe_audio(audio_path):
    with open(audio_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text


#get video transcription if available
def get_video_transcript(video_url):
    video_id = video_url.split("v=")[-1]
    try:
        transcript = YouTubeTranscriptApi.list_transcripts(video_id)
        print("transcript original" , transcript)
    except TranscriptsDisabled:
        print("TranscriptsDisabled" , TranscriptsDisabled)
        return None

    text = " ".join([line["text"] for line in transcript])
    return text



def split_text_into_chunks(text, chunk_size=2048):
    words = text.split()
    #print(words)
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]



def summarize_text(text, language, summary_type):
    chunks = split_text_into_chunks(text)
    chunk_summaries = []

    for chunk in chunks:
        chunk_summaries.append(chunk)
    combined_text = " ".join(chunk_summaries)

    print(combined_text)
    final_prompt = f"Generate a {summary_type.lower()} summary in {language} of the following text:\n{combined_text}"
    final_completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": final_prompt}],
        max_tokens=1000 if summary_type.lower() == 'detailed' else 100,
        temperature=0.7
    )
    
    return final_completion.choices[0].message.content



@app.route('/summarize', methods=['POST'])
def summarize_video():
    data = request.json
    video_url = data.get('youtube_video_url')
    language = data['language']  
    type_of_summary = data['type_of_summary']  

    # Step 1: Attempt to get YouTube video transcript
    transcript = get_video_transcript(video_url)
    
    # Step 2: If transcript is unavailable, download and transcribe audio
    if not transcript:
        try:
            audio_path = download_audio(video_url)
            print(audio_path)
            transcript = transcribe_audio(audio_path)
            print(transcript)
        except Exception as e:
            print("eeeeee")
            return jsonify({'error': str(e)}), 500
        

    # Step 3: Summarize the transcript
    summary = summarize_text(transcript, language, type_of_summary)
    
    return jsonify({'summary': summary})



if __name__ == '__main__':
    app.run(debug=True)
