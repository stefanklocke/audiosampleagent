import struct
import io
import re
import operator
import json
from pathlib import Path
import os

import pandas as pd

from pathlib import Path
import os

pd.set_option('display.max_columns', None)

class WAVFile:

    def __init__(self, filename):
        self.filename = filename

    def read(self, report_chunk_info = False, report_chunk_clean = False, report_lists = False):
        def extract_tags(chunk_decoded_clean, tags_type = "flags"):
            if(tags_type == "flags"):
                # ASSUMPTION: part with @-flags starts with \x07\x07 and end with end of string
                chunk_flags = re.search(r"\x07\07.*", chunk_decoded_clean).group(0)
                # split at control sequences
                chunk_flags_split = re.split('([\x01-\x1f]+)', chunk_flags)
                # remove first (empty) element
                chunk_flags_split = chunk_flags_split[1:len(chunk_flags_split)]
                # replace "\x07\x07" by "\x07", bearing in mind that toplevel address of flags is \x07 (the first "\x07")
                chunk_flags_split[0] = "\x07"
                
                k = 4
                i_max = int(len(chunk_flags_split) / k)
                ans = list()
                for i in range(0, i_max):
                    res = operator.getitem(chunk_flags_split, slice(i*k, k*(i+1)))

                    flag = {
                        "name": res[1],
                        "value": res[3],
                        "addresses": {
                            "name": res[0],
                            "value": res[2]
                        }
                    }
                    
                    ans.append(flag)

                return(ans)
            else:
                raise ValueError("Currently, only tags_type = 'flags' is allowed.")

        with io.open(self.filename, 'rb') as fh:
            chunk = fh.read(12)
            if(report_chunk_info):
                print("Unpacking from:", chunk)
            riff, size, fformat = struct.unpack('<4sI4s', chunk)
            if(report_chunk_info):
                print("Chunk ID: %s, Chunk Size: %i, Format: %s" % (riff, size, fformat))

            chunkOffset = fh.tell()
            while(chunkOffset < size):
                fh.seek(chunkOffset)

                chunk = fh.read(8)
                chunkID, chunkSize = struct.unpack('<4sI', chunk)
                
                if(report_chunk_info):
                    print("\t", "chunk id: %s, size: %i" % (chunkID, chunkSize))

                if(chunkID == b'\x00ID3' or chunkID == b'ID3 '):
                    chunk = fh.read(chunkSize)
                    print(chunk)
                    chunk_decoded = chunk.decode("utf-8", errors = "ignore")

                    print(chunk_decoded)

                    chunk_decoded_clean = chunk_decoded.replace("\x00", "")

                    if(chunk_decoded_clean[0:3] == "ID3"):
                        chunk_decoded_clean = chunk_decoded_clean[3:]
                    else:
                        raise ValueError("Chunk did not start with 'ID3', something went wrong!")

                    chunk_decoded_clean_ls = re.split('([\x01-\x1f]+)', chunk_decoded_clean)
                    del chunk_decoded_clean_ls[0]

                    print("\n")
                    # print(repr(re.split(r'(\x04\x0b.*) (com)', chunk_decoded_clean)))
                    def junk_filter(x):
                        if(x == ""):
                            return False
                        elif(x == "*"):
                            return False
                        elif(x == "\r"):
                            return False
                        else:
                            return True

                    split = re.split(r'(\x04\x0b)(.*)(\x04)([*]?)(.*)(\x02\x01)(\r?)(.*)(\x12)(.*)(\x12)(.*)(\x01\01)(.*)', chunk_decoded_clean)
                    print("Split before filter:\n", repr(split), "\n")
                    print("Split after filter:\n", repr(list(filter(junk_filter, split))), "\n")

                    if(report_chunk_clean):
                        print("Raw chunk (no decoding):\n", repr(chunk), "\n")
                        print("Decoded chunk:\n", repr(chunk_decoded), "\n")
                        print("Decoded chunk (cleaned):\n", repr(chunk_decoded_clean), "\n")
                        print("Split chunk (list):\n", chunk_decoded_clean_ls, "\n")

                        chunk_flags_dict = extract_tags(chunk_decoded_clean)
                        # print("Flags Chunk (dict):\n", chunk_flags_dict, "\n")
                        print("Flags Chunk (dict):\n", json.loads(json.dumps(chunk_flags_dict, sort_keys=True, indent=4)), "\n")


                    even = list(range(0, len(chunk_decoded_clean_ls), 2))
                    odd = list(range(1, len(chunk_decoded_clean_ls), 2))

                    # Remove first value "ID3" because its the chunk name
                    chunk_values = [chunk_decoded_clean_ls[i] for i in odd]
                    # del chunk_values[0]
                    chunk_addresses = [chunk_decoded_clean_ls[i].encode('unicode_escape') for i in even]
                    print("Chunk values:\n", chunk_values)
                    print("Chunk addresses:\n", chunk_addresses, "\n")

                    dict_label = {
                        "address": [
                            b"\\x04\\x0b",          # e.g. PGEOB
                            b"\\x04",               # com.native-instruments.nisound.soundinfo

                        ],
                        "label": [
                            "Header",               # e.g. PGEOB
                            "Header-NI Soundinfo"   # com.native-instruments.nisound.soundinfo
                        ]
                    }
                    
                    labels = [
                        "Header",
                        "Header-NI Soundinfo",
                        "Name",
                        "Properties-Vendor",
                        "Properties-Author",
                        "General-Product",
                        "General-Content Type",
                        "Types",
                        "@color flag",
                        "@color value",
                        "@devicetypeflags flag",
                        "@devicetypeflags value",
                        "@soundtype flag",
                        "@soundtype value",
                        "@tempo flag",
                        "@tempo value",
                        "@verl flag",
                        "@verl value",
                        "@verm flag",
                        "@verm value",
                        "@visib flag",
                        "@visib value"
                    ]
                    # ['\x04\x14', # Soundinfo Header
                    #  '\x02\x01\x18', # Name
                    #  '\x12', # Properties-Vendor
                    #  '\x12', # Properties-Author
                    #  '\x01\x01\x0b', # General-Product
                    #  '\x02\x07', # General-Content Type
                    #  '\x0e', # Types = Synth
                    #  '\x07\x07', # @color flag
                    #  '\x01', # @color value
                    #  '\x11', # @devicetypeflags flag
                    #  '\x01', # @devicetypeflags value
                    #  '\x0b', # @soundtype flag
                    #  '\x01', # @soundtype value
                    #  '\x07', # @tempo flag
                    #  '\x01', # @tempo value
                    #  '\x06', # @verl flag
                    #  '\x06', # @verl value
                    #  '\x06', # @verm flag
                    #  '\x06', # @verm value
                    #  '\x07', # @visib flag
                    #  '\x01' # @visib value
                    #  ]
                    # ['com.native-instruments.nisound.soundinfo',
                    #  'Modular[122] F#m Miko 1.wav',
                    #  'Native Instruments',
                    #  'Native Instruments',
                    #  'Deep Matter',
                    #  '\\:Loops',
                    #  '\\:Loops\\:Synth',
                    #  '\\@color',
                    #  '0',
                    #  '\\@devicetypeflags',
                    #  '0',
                    #  '\\@soundtype',
                    #  '0',
                    #  '\\@tempo',
                    #  '0',
                    #  '\\@verl',
                    #  '1.7.14',
                    #  '\\@verm',
                    #  '1.7.14',
                    #  '\\@visib',
                    #  '0']

                    print("Labels:", len(labels), "addresses:", len(chunk_addresses), "Values:", len(chunk_values))

                    if(len(labels) < len(chunk_addresses)):
                        labels = [""] * (len(chunk_addresses) - len(labels)) + labels

                    if(report_lists):
                        print(labels)
                        print(chunk_addresses)
                        print(chunk_values)
                    
                    df = pd.DataFrame({
                        "filename": [self.filename] * len(labels),
                        "label": labels,
                        "address": chunk_addresses,
                        "value": chunk_values
                    })

                else:
                    df = None

                chunkOffset = chunkOffset + chunkSize + 8

        return(df)

print(os.getcwd())

# wavFile = WAVFile('Modular[122] F#m Miko 1.wav')
wavFile = WAVFile(Path('./data/Ambience Berlina 6.wav'))

# wavFile = WAVFile('aah_chord_loop_contact_120_Cmin.wav')
wavFile = WAVFile(Path(os.getcwd(), "data", "Instr_34_Smp_00.wav"))
wavFile.read()
# wavFile = WAVFile('aah_chord_loop_elektron_120_Gmin.wav')
wavFile.read()