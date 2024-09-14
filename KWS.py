from pydub import AudioSegment
import speech_recognition as sr
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# Initialize recognizer
recognizer = sr.Recognizer()

def preprocess_audio(input_file, output_file):
    """
    Convert and preprocess the audio file to ensure it's in the correct format and sample rate.
    """
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(16000)  # Set standard sample rate
    audio = audio.set_channels(1)  # Ensure mono
    audio.export(output_file, format="wav")

def audio_to_text(audio_file, language='en-US'):
    """
    Convert audio file to text using SpeechRecognition with language support.
    """
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        print("Audio successfully read from file.")
        try:
            text = recognizer.recognize_google(audio, language=language)
            print(f"Recognized text: {text}")
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None
    except Exception as e:
        print(f"Failed to read audio file: {e}")
        return None

def detect_keywords(transcription, keywords):
    """
    Check if each keyword is present in the transcription and return their start and end times.
    """
    keyword_intervals = []
    detected_keywords = []
    keyword_positions = {keyword: [] for keyword in keywords}
    if transcription:
        transcription = transcription.lower()
        for keyword in keywords:
            keyword = keyword.lower()
            start = transcription.find(keyword)
            if start != -1:
                end = start + len(keyword)
                keyword_intervals.append((keyword, start, end))
                detected_keywords.append(keyword)
                keyword_positions[keyword].append((start, end))
            else:
                print(f"Keyword '{keyword}' not found.")
    return keyword_intervals, detected_keywords, keyword_positions

def compute_accuracy(detected_keywords, keywords):
    """
    Compute precision, recall, and F1 score based on detected and expected keywords.
    """
    true_positives = len(set(detected_keywords) & set(keywords))
    false_positives = len(detected_keywords) - true_positives
    false_negatives = len(keywords) - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return precision, recall, f1_score

def compute_individual_keyword_metrics(keyword_positions, keywords):
    """
    Compute precision, recall, and F1 score for each individual keyword.
    """
    keyword_metrics = {}
    for keyword in keywords:
        true_positives = len(keyword_positions.get(keyword, []))
        false_positives = sum(len(keyword_positions.get(k, [])) for k in keyword_positions if k != keyword)
        false_negatives = 1 if true_positives == 0 else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        keyword_metrics[keyword] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    
    return keyword_metrics

def plot_waveform_with_keywords(audio_file, keyword_intervals_in_time):
    """
    Plot the waveform of the audio file with highlighted keyword intervals.
    """
    # Read the audio file
    sample_rate, data = wavfile.read(audio_file)
    data = data.astype(float)  # Convert data to float for better plotting
    
    # Time axis
    N = len(data)
    T = 1.0 / sample_rate
    x = np.linspace(0.0, N*T, N)
    
    # Plot the waveform
    plt.figure(figsize=(12, 8))
    plt.plot(x, data, label='Waveform', color='b')

    # Highlight keyword intervals
    for keyword, start, end in keyword_intervals_in_time:
        plt.axvspan(start, end, color='yellow', alpha=0.5, label=f'Keyword: {keyword}')
    
    plt.title('Waveform with Keyword Intervals')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    
    plt.tight_layout()
    plt.show()

def main(input_audio_file, output_audio_file, keywords, language='en-US'):
    """
    Main function to preprocess the audio file, convert to text, detect keywords, and analyze audio.
    """
    # Preprocess the audio file
    preprocess_audio(input_audio_file, output_audio_file)
    
    # Convert audio to text
    transcription = audio_to_text(output_audio_file, language)
    
    if transcription:
        print(f"Transcription: {transcription}")
        # Check if the keywords are present in the transcription
        keyword_intervals, detected_keywords, keyword_positions = detect_keywords(transcription, keywords)
        
        # Compute overall accuracy
        precision, recall, f1_score = compute_accuracy(detected_keywords, keywords)
        print(f"Overall Precision: {precision:.2f}")
        print(f"Overall Recall: {recall:.2f}")
        print(f"Overall F1 Score: {f1_score:.2f}")

        # Compute individual keyword metrics
        keyword_metrics = compute_individual_keyword_metrics(keyword_positions, keywords)
        for keyword, metrics in keyword_metrics.items():
            print(f"Keyword '{keyword}':")
            print(f"  Precision: {metrics['precision']:.2f}")
            print(f"  Recall: {metrics['recall']:.2f}")
            print(f"  F1 Score: {metrics['f1_score']:.2f}")
            print(f"  True Positives: {metrics['true_positives']}")
            print(f"  False Positives: {metrics['false_positives']}")
            print(f"  False Negatives: {metrics['false_negatives']}")
        
        # Calculate total duration of the audio in seconds
        sample_rate, _ = wavfile.read(output_audio_file)
        audio_duration = len(_) / sample_rate
        
        # Convert keyword intervals to audio time
        keyword_intervals_in_time = [(keyword, start / len(transcription) * audio_duration, (end) / len(transcription) * audio_duration) for keyword, start, end in keyword_intervals]
        
        # Plot the waveform with keyword intervals
        plot_waveform_with_keywords(output_audio_file, keyword_intervals_in_time)
        
        # Print the timestamps of the keywords
        for keyword, start, end in keyword_intervals_in_time:
            print(f"Keyword '{keyword}' found between {start:.2f} and {end:.2f} seconds.")
    else:
        print("No transcription available. Check if the audio file contains clear speech and is in a compatible format.")

# Example usage
input_audio_file = "/Users/neeraj/Desktop/NEERAJ/SIH/Telugu_Voice.mp3"  # Specify your file path
output_audio_file = "processed_audio.wav"
keywords = ["నీ రాజ్"]  # List of keywords to detect
language = 'te'  # Specify the language code
main(input_audio_file, output_audio_file, keywords, language)