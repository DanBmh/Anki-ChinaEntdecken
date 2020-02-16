import hashlib
import json
import os
import shutil

import pandas as pd
import tqdm

import create_voice_data

# ======================================================================================================================

add_note_id = True
add_strokes_gif = True
delete_duplicates = True
add_audio_files = True
override_existing_audio_files = False

# Not in "Most Common 3000 Chinese" deck, they have to copied from "Domino_Chinese" deck or downloaded by hand
extra_gifs = {
    "橙": "27225.gif",
    "饺": "39290.gif",
    "梨": "26792.gif",
    "醋": "37259.gif",
    "皂": "30338.gif",
    "蕉": "34121.gif",
    "剃": "yellowbridge_1.gif",
    "嘘": "yellowbridge_2.gif"
}
extra_audio = {
    "还": "1bc709b8bf6c9706fa662b82b775e542bdf7c6ec0c044bea85def6f0eeea0158.mp3",
    "着": "9e5bf0d2d993accb3cb434261e9d1ffbaca44ffe38de817324ea53178fc00cb2.mp3",
}

file_path = os.path.dirname(os.path.realpath(__file__)) + "/"
vocab_path = file_path + "Anki-ChinaEntdecken.json"
mch_path = file_path + "../Most Common 3000 Chinese - ANKI with Traditional.csv"

# ======================================================================================================================

with open(vocab_path, mode="r", encoding="utf-8") as file:
    content = json.load(file)

mch_data = pd.read_csv(mch_path, header=None, keep_default_na=False)
added_gifs = []
added_audios = []

notes = content["notes"]
for i, note in enumerate(tqdm.tqdm(notes)):
    if (add_note_id):
        # Create note id from hashed simplified field 
        note["guid"] = hashlib.sha256(note["fields"][0].encode('utf-8')).hexdigest()

    if (add_strokes_gif):
        simp = note["fields"][0]
        text = ""

        for s in simp:
            if (s in " ."):
                # Skip some of the keys
                continue

            if (s in extra_gifs):
                # Handle gifs added by hand
                t = "<img src='{}' />".format(extra_gifs[s])
            else:
                try:
                    # Search for the matching gif
                    t = mch_data[mch_data.iloc[:, 0] == s].iloc[0, 2]
                except IndexError:
                    print("For this key there is no entry:", s)

            t = t.replace(" />", "/>")
            t = t.replace("img src", "img class=\"animated-gif\" src")
            text = text + t

            g = t.partition("src=\'")[2].partition(".gif")[0] + ".gif"
            added_gifs.append(g)

        if (len(note["fields"]) == 4):
            note["fields"].append(text)
        elif (len(note["fields"]) > 4):
            note["fields"][4] = text
        else:
            print("This note has not enough fields")
            raise ValueError

    if (add_audio_files):
        simp = note["fields"][0]
        audio_name = note["guid"] + ".mp3"
        audio_path = file_path + "media/" + audio_name

        if (not simp in extra_audio):
            if (override_existing_audio_files or len(note["fields"]) == 5 or
                    (len(note["fields"]) > 5 and note["fields"][5] == "")):
                # Skip only the audio download if the file is already existing but not the rest,
                # the audio_name is used later to add the files to the decks media field
                create_voice_data.download(simp, audio_path)
        else:
            audio_name = extra_audio[simp]

        text = "[sound:{}]".format(audio_name)
        added_audios.append(audio_name)

        if (len(note["fields"]) == 5):
            note["fields"].append(text)
        elif (len(note["fields"]) > 5):
            note["fields"][5] = text
        else:
            print("This note has not enough fields")
            raise ValueError

if (add_note_id and delete_duplicates):
    # Delete duplicates which got somehow in the deck, 
    # new notes have to get the right id before else they may get deleted as the guid is copy pasted from other notes
    print("Deleting duplicates ...")

    for i, note in enumerate(notes):
        for j, n in enumerate(notes[i + 1:]):
            if (note["guid"] == n["guid"]):
                notes.pop(i + 1 + j)

if (add_strokes_gif):
    # Copy gif files
    print("Copying gif files ...")

    src_path_1 = file_path + "../Domino_Chinese_Level_1-20_Complete_Vocabulary/media/"
    src_path_2 = file_path + "../Chinese__Most_Common_3000_Hanzi/media/"
    dest_path = file_path + "media/"
    for g in added_gifs:
        if (not os.path.isfile(dest_path + g)):
            if (os.path.isfile(src_path_1 + g)):
                shutil.copy(src_path_1 + g, dest_path)
            elif (os.path.isfile(src_path_2 + g)):
                shutil.copy(src_path_2 + g, dest_path)
            else:
                print("No file to copy gif:", g)

if (add_audio_files or add_strokes_gif):
    # Add names of audio files and gif files to deck description

    added_gifs = sorted(list(set(added_gifs)))
    added_audios = sorted(list(set(added_audios)))
    media_files = added_gifs
    media_files.extend(added_audios)
    content["media_files"] = media_files

# Write the deck back to file
with open(vocab_path, mode="w", encoding="utf-8") as file:
    json.dump(content, file, ensure_ascii=False, indent=4, sort_keys=True)
