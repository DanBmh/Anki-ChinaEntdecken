import json
import os
import hashlib
import pandas as pd
import shutil

add_note_id = True
add_strokes_gif = True
delete_duplicates = True

# Not in "Most Common 3000 Chinese" deck, they have to copied from "Domino_Chinese" deck or downloaded by hand
extra_gifs = {
    "橙":"27225.gif",
    "饺":"39290.gif",
    "梨":"26792.gif",
    "醋":"37259.gif",
    "皂":"30338.gif",
    "蕉":"34121.gif",
    "剃":"yellowbridge_1.gif",
    "嘘":"yellowbridge_2.gif"
}

file_path = os.path.dirname(os.path.realpath(__file__)) + "/"
vocab_path = file_path + "Anki-ChinaEntdecken.json"
mch_path = file_path + "../Most Common 3000 Chinese - ANKI with Traditional.csv"

with open(vocab_path, mode="r", encoding="utf-8") as file:
    content = json.load(file)

mch_data = pd.read_csv(mch_path, header=None, keep_default_na=False)
added_gifs = []

notes = content["notes"]
for i, note in enumerate(notes):
    if(add_note_id):
        # Create note id from hashed simplified field 
        note["guid"] = hashlib.sha256(note["fields"][0].encode('utf-8')).hexdigest()
    
    if(add_strokes_gif):
        simp = note["fields"][0]
        text = ""
        
        for s in simp:
            if(s in " ."):
                # Skip some of the keys
                continue

            if(s in extra_gifs):
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

        if(len(note["fields"]) == 4):
            note["fields"].append(text)
        elif(len(note["fields"]) > 4):
            note["fields"][4] = text
        else:
            print("This note has not enough fields")
            raise ValueError


if(add_note_id and delete_duplicates):
    # Delete duplicates which got somehow in the deck, 
    # new notes have to get the right id before else they may get deleted as the guid is copy pasted from other notes

    for i, note in enumerate(notes):
        for j, n in enumerate(notes[i+1:]):
            if(note["guid"] == n["guid"]):
                notes.pop(i+1+j)

if(add_strokes_gif):
    # Copy gif files and add names to deck description

    added_gifs = sorted(list(set(added_gifs)))
    content["media_files"] = added_gifs

    src_path_1 = file_path + "../Domino_Chinese_Level_1-20_Complete_Vocabulary/media/"
    src_path_2 = file_path + "../Chinese__Most_Common_3000_Hanzi/media/"
    dest_path = file_path + "media/"
    for g in added_gifs:
        if(not os.path.isfile(dest_path + g)):
            if(os.path.isfile(src_path_1 + g)):
                shutil.copy(src_path_1 + g, dest_path)
            elif(os.path.isfile(src_path_2 + g)):
                shutil.copy(src_path_2 + g, dest_path)
            else:
                print("No file to copy gif:", g)

# Write the deck back to file
with open(vocab_path, mode="w", encoding="utf-8") as file:
    json.dump(content, file, ensure_ascii=False, indent=4, sort_keys=True)