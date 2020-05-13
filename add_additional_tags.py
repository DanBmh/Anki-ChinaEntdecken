import hashlib
import json
import os
import re
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
# Search https://www.mdbg.net/chinese/dictionary or https://www.yellowbridge.com/chinese/dictionary.php
extra_gifs = {
    "勺": "21242.gif",
    "梨": "26792.gif",
    "椒": "26898.gif",
    "橙": "27225.gif",
    "皂": "30338.gif",
    "筷": "31607.gif",
    "蒜": "33948.gif",
    "蕉": "34121.gif",
    "酱": "37233.gif",
    "醋": "37259.gif",
    "饺": "39290.gif",
    "剃": "yellowbridge_1.gif",
    "嘘": "yellowbridge_2.gif"
}
extra_audio = {
    "还": "2200b793c7badc792f9d2fdd016f84c16a4970c5a031fd2693b122e739d54258.mp3",
    "着": "7df1a76a6505e8f48791bb8c6f33772e61132eacbb673d08862e3ddfc49a6fee.mp3",
}

file_path = os.path.dirname(os.path.realpath(__file__)) + "/"
vocab_path = file_path + "Anki-ChinaEntdecken.json"
mch_path = file_path + "../Most Common 3000 Chinese - ANKI with Traditional.csv"

if (add_audio_files):
    create_voice_data.init_client()


# ======================================================================================================================

def generate_note_id(note):
    """ Create id from hashed simplified and chapter tag.
    The chapter tag is used to differentiate between words with same sign and multiple meanings,
      which are added later in the book. So the vocabulary doesn't differ from the one in the book.
    The translation field instead of the chapter tag can't be used, to prevent changes in the ids 
      if an error in the translation is fixed. """

    for t in note["tags"]:
        if("Buch" in t):
            text = t

    text = note["fields"][0] + text
    note_id = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return note_id


# ======================================================================================================================

def get_gifs(note):
    """ Generate the gif text and collect the gif paths """

    simp = note["fields"][0]
    text = ""
    gifs = []

    for s in simp:
        if (s in " ."):
            # Skip some of the keys
            continue

        t = None
        if (s in extra_gifs):
            # Handle gifs added by hand
            t = "<img src='{}' />".format(extra_gifs[s])
        else:
            try:
                # Search for the matching gif
                t = mch_data[mch_data.iloc[:, 0] == s].iloc[0, 2]
            except IndexError:
                print("For this key there is no gif entry:", s)

        if not t is None:
            t = t.replace(" />", "/>")
            t = t.replace("img src", "img class=\"animated-gif\" src")
            text = text + t

            g = t.partition("src=\'")[2].partition(".gif")[0] + ".gif"
            gifs.append(g)

    return text, gifs


# ======================================================================================================================

def get_audio_file(note):
    """ Download the audiofile and return audio text and path """

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
    return text, audio_name


# ======================================================================================================================


with open(vocab_path, mode="r", encoding="utf-8") as file:
    content = json.load(file)

mch_data = pd.read_csv(mch_path, header=None, keep_default_na=False)
added_gifs = []
added_audios = []

notes = content["notes"]
for i, note in enumerate(tqdm.tqdm(notes)):
    if (add_note_id):
        note["guid"] = generate_note_id(note)

    if (add_strokes_gif):
        text, gifs = get_gifs(note)
        added_gifs.extend(gifs)

        if (len(note["fields"]) == 4):
            note["fields"].append(text)
        elif (len(note["fields"]) > 4):
            note["fields"][4] = text
        else:
            print("This note has not enough fields")
            raise ValueError

    if (add_audio_files):
        text, audio_name = get_audio_file(note)
        added_audios.append(audio_name)

        if (len(note["fields"]) == 5):
            note["fields"].append(text)
        elif (len(note["fields"]) > 5):
            note["fields"][5] = text
        else:
            print("This note has not enough fields")
            raise ValueError

if (add_note_id):
    # Search or delete duplicates which got somehow in the deck, 
    # New notes have to get the right id before, else they may get deleted as the guid is copy pasted from other notes
    if(delete_duplicates):
        print("Deleting duplicates ...")
    else:
        print("Searching duplicates ...")

    for i, note in enumerate(notes):
        for j, n in enumerate(notes[i + 1:]):
            if (note["guid"] == n["guid"]):
                if(delete_duplicates):
                    notes.pop(i + 1 + j)
                else:
                    print("Found duplicate:", note["fields"][0], note["fields"][2])
            if (note["fields"][0] == n["fields"][0]):
                msg = "Found same signs:\n  {}: {}\n  {}: {}"
                msg = msg.format(note["fields"][0], note["fields"][2],n["fields"][0], n["fields"][2])
                print(msg)


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
