"""
Notes:
- mutage.File().tags contains object of class 'mutagen.wave._WaveID3'
- _WaveID3


Some links:
https://mutagen.readthedocs.io/en/latest/api/id3_frames.html#mutagen.id3.GEOB
"""

import mutagen
from pathlib import Path
import pprint
from collections import namedtuple

pp = pprint.PrettyPrinter(indent=4)

pathData = Path("./data")
files = [
    "aah_chord_loop_contact_120_Cmin.wav",
    "aah_chord_loop_elektron_120_Gmin.wav",
    "Ambience Berlina 6.wav",
    "Instr_34_Smp_00.wav",
    "Modular[122] F#m Miko 1.wav"
]

a = mutagen.File(Path(pathData, "aah_chord_loop_contact_120_Cmin.wav"))

# print(a.tags.__dir__())

# print(a.tags.keys())
# # a.tags.size -- number of bytes of GEOB (or ID3?) part
# # a.tags.keys() -- returns dict_keys() object (standard object from dict), iterable




def run_files(files, folder = Path("./data")):
    def get_tags(file):
        # Empty list will be returned as default (if file.tags is None)
        ans = []
        tags = file.tags

        if(tags):
            # tags.items() returns a tuple with ("GEOB:...", GEOB(...))
            # The second element contains the actual frame, so this will be returned
            # ans = [tup[1] for tup in tags.items()]
            ans = [{"desc": tup[1].desc, "obj": tup[1]} for tup in tags.items()]
            return(ans)
        else:
            return(ans)

    
    ans = []

    for file in files:
        a = mutagen.File(Path(folder, file))

        # pp.pprint(a.tags.keys() if a.tags else None)
        current = {
            "filename": file,
            "tags": get_tags(a)
        }
        ans.append(current)
    
    return ans

audiofiles = run_files(files, pathData)
# audiofiles[0]["tags"][0][1] -- frame (in this case: GEOB frame)
# audiofiles[0]["tags"][0][1].FrameID -- returns frame ID (in this case: GEOB)
# audiofiles[0]["tags"][0][1].pprint() -- would print data, if data wasnt proprietary ...
# audiofiles[0]["tags"][0][1].data -- frame data
# pp.pprint(audiofiles)


for file in audiofiles:
    print(file["filename"])
    if(file["tags"]):
        for tag in file["tags"]:
            if(tag["desc"] == "com.native-instruments.nisound.soundinfo"):
                print(tag["obj"].data)

# # GEOBs
# for i in a.tags.keys():
#     if(i.startswith("GEOB")):
#         print("Hello")

# # GEOB 1
# print(a.tags["GEOB:com.native-instruments.nks.soundinfo"].data)

# \x88
# 	\xad
# 		__ni_internal
# \x81
# 	\xa6
# 		source
# 	\xa5
# 		other
# 	\xa6
# 		author
# 	\xac
# 		Sample Magic
# 	\xa7
# 		comment
# 	\xa0
# 	\xa5
# 		modes
# 		\x92
# 			\xa6
# 				Bright
# 			\xa5
# 				Chord
# 			\xa4
# 				name
# 			\xbf
# 				aah_chord_loop_contact_120_Cmin
# 			\xa5
# 				tempo
# 			\xcb
# 				\x00\x00\x00\x00\x00\x00\x00\x00
# 			\xa5
# 				types
# 			\x91
# 				\x91
# 					\xa9
# 						Synth Pad
# 					\xa6
# 						vendor
# 					\xa6
# 						Splice

# # GEOB 2
# print(a.tags["GEOB:com.native-instruments.nisound.soundinfo"].data)