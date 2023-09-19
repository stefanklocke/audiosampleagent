import test_new

filenames = [
    'E:\\MUSIC PRODUCTION\\Content\\Native Instruments\\Deep Matter\\Samples\\Drums\\Clap\\Clap Alecia 1.wav',
    "C:\\Users\\Stefan\\Desktop\\RIFF\\Modular[122] F#m Miko 1.wav"
]

wavFile = test_new.WAVFile(filenames[0])
wavFile.read(report_chunk_info = True, report_chunk_clean = True, report_lists = True)