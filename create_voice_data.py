"""
For setup follow:
https://cloud.google.com/text-to-speech/docs/reference/libraries

Export credentials in Powershell:
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\Studium\Chinesisch\AnkiDecks\Anki-ChinaEntdecken\google_application_credentials.json"
Export credentials in Linux:
export GOOGLE_APPLICATION_CREDENTIALS="`pwd`/google_application_credentials.json"

In rare cases audio is not correct, conversion to mp3 has to be done manually then. 
You can use this websites:
https://ttsmp3.com/text-to-speech/Chinese%20Mandarin/
https://www.eguidedog.net/ekho.php 
"""

import argparse
import random
import time

from google.cloud import texttospeech

# ==================================================================================================

client = None
speakers = [
    "cmn-CN-Wavenet-A",
    "cmn-CN-Wavenet-B",
    "cmn-CN-Wavenet-C",
    "cmn-CN-Wavenet-D",
]


# ==================================================================================================


def init_client():
    global client
    client = texttospeech.TextToSpeechClient()


# ==================================================================================================


def download(text, path):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    # Build the voice request
    voice = texttospeech.types.VoiceSelectionParams(
        language_code="cmn-CN", name=random.choice(speakers)
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary.
    with open(path, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    # Dont run more than 300 requests per min
    time.sleep(0.2)


# ==================================================================================================


def main():
    parser = argparse.ArgumentParser(description="Download spoken text")
    parser.add_argument("text", type=str)
    parser.add_argument("output_path", type=str)
    args = parser.parse_args()

    init_client()
    download(args.text, args.output_path)


# ==================================================================================================


if __name__ == "__main__":
    main()
