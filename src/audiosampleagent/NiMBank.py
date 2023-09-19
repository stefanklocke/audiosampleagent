#!/usr/bin/env python

import sys, getopt, os, mmap, struct, binascii, codecs, string, platform
import umsgpack, json
import codecs
import ctypes as ct
_debug=0
_verbose=0

__version__ = '4.2'
# 4.2 : Test if file is NI hsin/dsin file
# 4.1 : Change decode data : struct.unpack to int.from_bytes
# 4.0 : Add nrkt file (Reaktor file)
# 4.0 : Modify search data in file
# 4.0 : Modify hsin length indication
# 4.0 : Modify bank/subbank modification
# 4.0 : Add Correct hsin length process for file modify before v4.0 (--niheaderCorrect)
# 3.0e: Update umsgpack to v2.7.2
# 3.0e: Bug Correct modify_nisi_NKSF clear subbank
# 3.0d: Bug Correct bytes-like object is required, not 'str'
# 3.0d: Add Battery support (*.nkbd file)
# 3.0c: Migrate to Github
# 3.0b: Compatible to Python 3 - Correct Bank & Subbank modification
# 3.0a: Update umsgpack to 2.7.1
# 2.8g: Add FM8 support
# 2.8f: Bug Correct list & modify corrupt NKS files (bank/subbank/uuid)
# 2.8e: Add clear Macro for nks files
# 2.8d: Bug Correct header file length
# 2.8c: Bug Windows MMP... No tested on Windows OS 
# 2.8b: Correct bug (export_map)
# 2.8 : ADD create nksf from preset 
# 2.8 : ADD nksf nksfx support
# 2.7 : Correct Delete NKS map & Correct minor bug
# 2.6 : ADD NKS map to massive file (nmsv)
# 2.5 : Import/Export NKS data for nksm and nki FIle
# 2.4 : Add nksn support (snapshoot)
# 2.3 : Tag reader... AT WORK.
# 2.2 : Add nkm & nki support (Kontakt file)
# 2.0 : Add option delete Maschine Macro description for Massive files - Add mxprj support
# 1.9 : Correction file corrupt if modify author & vendor
# 1.8 : Add csv and xml export file information
# 1.7 : Add name, vendor, author, comment add/delete/modification
# 1.6 : Reorganize code
# 1.5 : Add Massive support
# 1.4 : Add Sub Bank
# 1.3 : Recursive Mode
# 1.2 : Stable version

try:
    unichr
except NameError:
    unichr = chr

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   WHITE = '\033[97m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
   FILE = '\033[0m\033[1m\033[93m'
   ERROR = '\033[0m\033[41m'
   OK = '\033[0m\033[44m'
   WARNING = '\033[0m\033[43m'

def debugtrace(trace):
  print(trace)

def shortFile(file):
	return os.path.basename(file)

def deleteFromMmap(f,start,end):
  global VDATA
  length = end - start
  size = len(VDATA)
  newsize = size - length
  VDATA.move(start,end,size-end)
  VDATA.flush()
  VDATA.close()
  f.truncate(newsize)
  VDATA = mmap.mmap(f.fileno(),0)

def insertIntoMmap(f,offset,data):
  global VDATA
  length = len(data)
  size = len(VDATA)
  newsize = size + length
  VDATA.flush()
  VDATA.close()
  f.seek(size)
  f.write("A"*length)
  f.flush()
  VDATA = mmap.mmap(f.fileno(),0)
  VDATA.move(offset+length,offset,size-offset)
  VDATA.seek(offset)
  VDATA.write(data)
  VDATA.flush()

def AddSizeOfFile(f):
  global VDATA
  size = struct.pack('<I', len(VDATA))
  if _debug: debugtrace("New lenght file : " + str(len(VDATA)))
  deleteFromMmap(f,0,4)
  insertIntoMmap(f,0,size)

def RIFF_update(fnks):
	global VDATA
	riff_start = VDATA.find(b'RIFF',0) + 4
	if _debug: debugtrace("NKS -> Riff start: " + str(riff_start))
	riff_nbcar = len(VDATA) - riff_start - 4
	if _debug: debugtrace("NKS -> Riff nb car: " + str(riff_nbcar))
	data = struct.pack('I', riff_nbcar)
	if _debug: debugtrace("NKS -> delete RIFF len - start:" + str(riff_start))
	deleteFromMmap(fnks, riff_start, riff_start + 4)
	if _debug: debugtrace("NKS -> INSERT NEW RIFF LEN - srart:" + str(riff_start))
	insertIntoMmap(fnks, riff_start, data)
  
def data_format(data):
#	test = b'\x00' + unichr(len(data)) + b'\x00\x00' + data.encode("utf_16_be")
	size = struct.pack('<I', len(data))
	data_format = size + data.encode("utf_16_le")
	return data_format

def hex2uint16(s): 
	# assumed s is up to four hex digits 
	i = eval('0x' + s) 
	if i >= 2**15: 
		i -= 2**16 
	return i 

def nbr_pair(nbr):
	if nbr%2 == 0 : return 1
	else : return 0

def nbr_impair(nbr):
	if nbr%2 == 0 : return 0
	else : return 1

def export_map_NKSF(filenks, filemap):
	global VDATA
	fnks =  open(filenks, 'r')
	fmap = open(filemap, "w")
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_READ)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
	curs = 0
	nica_nbcar = 0
	
	# SEARCH NICA
	curs = VDATA.find(b'NICA',0) 
	curs = curs + 4
	nica_nbcar = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	if _debug: debugtrace("nb Nica car:" + str(nica_nbcar))
	if _debug: debugtrace("curs:" + str(curs))
	nica_data=VDATA[curs:curs+nica_nbcar+4]
	fmap.write(nica_data)
	# ----------------
	# CLOSE FILE
	sys.stdout.flush()
	VDATA.close()
	fmap.close()
	fnks.close()
	return 1

def import_map_NKSF(filenks, filemap):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks =  open(filenks, 'a+')
	fmap = open(filemap , 'rb')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0
	nica_nbcar = 0
	if _debug : debugtrace("Remplace map")
	# SEARCH Subchunk NICA 
	# Modify NICA Data	
	curs = VDATA.find(b'NICA',0) 
	nica_start = curs + 4
	nica_nbcar = int.from_bytes(VDATA[nica_start:nica_start+4], "little", signed="False")
	if _debug: debugtrace("NKS -> nb Nica car:" + str(nica_nbcar))
	if _debug: debugtrace("NKS -> curs Nica Start:" + str(nica_start))
	if nbr_pair(nica_nbcar) == 0 : nica_nbcar = nica_nbcar + 1
	deleteFromMmap(fnks, nica_start, nica_start + nica_nbcar + 4)
	if _debug: debugtrace("NKS -> Deletat Nica")
	data = fmap.read()
	if nbr_pair(len(data)) == 0 : data = data + b'\x00'
	if _debug: debugtrace("MAP -> Read Map Data")
	insertIntoMmap(fnks, nica_start, data)
	if _debug: debugtrace("NKS -> Insert Map Data start " + str(nica_start))
	# Update RIFF Value
	RIFF_update(fnks)
	# ----------------
	# CLOSE FILE
	sys.stdout.write("*")
	sys.stdout.flush()
	VDATA.close()
	fmap.close()
	fnks.close()
	return 1

def create_NKSF(patchfile, patch_offset, nks_type):
	global VDATA
	data = ""
	with  open(patchfile, 'rb') as fpatch :
		if (platform.system() == "Windows") : VDATA = mmap.mmap(fpatch.fileno(),0, access=mmap.ACCESS_READ)
		else : VDATA = mmap.mmap(fpatch.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
		# Patch (delete patch_offset carac before importing to nks file)
		# for Union VST patch_offset=19
		if _debug: debugtrace("Patch Offset:" + patch_offset)
		data = VDATA[int(patch_offset):len(VDATA)]
		data = struct.pack('I', len(data)) + data

		namehead, nametail = os.path.split(patchfile)
		nametail = os.path.splitext(nametail)[0]
		if nks_type == "fx": nks_ext=".nksfx"
		else : nks_ext=".nksf"
		nksname = os.path.splitext(patchfile)[0] + nks_ext
		with open(nksname, "wb") as fnks :
			if _debug: debugtrace("Create nks file :" + nksname + ". Your plateform " + platform.system())
			# Patch name
			data = os.path.splitext(patchfile)[0].encode(encoding = 'UTF-8') + b'\x00' + data
			# PCHK Header
			data = b'\x01\x00\x00\x00' + data
			data = struct.pack('I', len(data)) + data
			data = "PCHK".encode(encoding = 'UTF-8') + data
			#NIKSNISI NICA (No NKS header)
			data = b'\x4E\x49\x4B\x53\x4E\x49\x53\x49\x80\x00\x00\x00\x01\x00\x00\x00\x87\xA6\x61\x75\x74\x68\x6F\x72\xA0\xA9\x62\x61\x6E\x6B\x63\x68\x61\x69\x6E\x91\xA5\x55\x6E\x69\x6F\x6E\xA7\x63\x6F\x6D\x6D\x65\x6E\x74\xA0\xAA\x64\x65\x76\x69\x63\x65\x54\x79\x70\x65\xA4\x49\x4E\x53\x54\xA4\x6E\x61\x6D\x65\xA7\x41\x6E\x76\x65\x72\x73\x65\xA4\x75\x75\x69\x64\xD9\x24\x36\x62\x38\x35\x65\x35\x31\x39\x2D\x31\x66\x61\x39\x2D\x34\x35\x34\x62\x2D\x61\x65\x39\x66\x2D\x64\x65\x31\x32\x39\x30\x63\x36\x35\x35\x62\x36\xA6\x76\x65\x6E\x64\x6F\x72\xA9\x53\x6F\x75\x6E\x64\x73\x70\x6F\x74\x4E\x49\x43\x41\x0A\x00\x00\x00\x01\x00\x00\x00\x81\xA3\x6E\x69\x38\x90\x50\x4C\x49\x44\x14\x00\x00\x00\x01\x00\x00\x00\x81\xA9\x56\x53\x54\x2E\x6D\x61\x67\x69\x63\xCE\x55\x6E\x31\x6F' + data
			# RIFF Header
			if nbr_impair(len(data)): data = data + b'\x00'
			data = struct.pack('I', len(data)) + data
			data = "RIFF".encode(encoding = 'UTF-8') + data
			fnks.write(data)
			# ----------------
			# CLOSE FILE
			sys.stdout.write("/")
			sys.stdout.flush()
	return nksname


def list_nks_NKSF(filenks):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'r')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_READ)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
	curs = 0
	nica_nbcar = 0
	nisi_nbcar = 0
	if _debug : debugtrace("List tag")
	# SEARCH NISI
	curs = 0 
	curs = curs + 4	
	nisi_start = curs
	nisi_nbcar = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	if _debug: debugtrace("NKS -> nb NISI car:" + str(nisi_nbcar))
	# Unpack msgpack (JSON)
	nisi_data=VDATA[nisi_start:nisi_nbcar]
	packer = umsgpack.unpackb(nisi_data)
	debugtrace(packer)	
	# ----------------
	# CLOSE FILE
	VDATA.close()
	fnks.close()
	return 1

def list_nisi_NKSF(filenks):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'r')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_READ)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
	curs = 0
	nica_nbcar = 0
	nisi_nbcar = 0
	if _debug : debugtrace("List tag")
	# SEARCH NISI
	curs = VDATA.find(b'NISI',0)
	curs = curs + 4
	nisi_start = curs
	nisi_nbcar = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	if _debug: debugtrace("NKS -> NISI start : " + str(nisi_start) + " - nb car:" + str(nisi_nbcar))
	# Go to NICA
	curs = VDATA.find(b'NICA',0)
	nica_start = curs + 4
	nica_nbcar = int.from_bytes(VDATA[nica_start:nica_start+4], "little", signed="False")
	if _debug: debugtrace("NKS -> NICA start : " + str(nica_start) + " - nb car:" + str(nica_nbcar))
	# Go to PLID
	curs = VDATA.find(b'PLID',0)
	plid_start = curs + 4
	plid_nbcar = int.from_bytes(VDATA[plid_start:plid_start+4], "little", signed="False")
	if _debug: debugtrace("NKS -> PLID start : " + str(plid_start) + " - nb car:" + str(plid_nbcar))
	# Go to PCHK
	curs = VDATA.find(b'PCHK',0)
	pchk_start = curs + 4
	pchk_nbcar = int.from_bytes(VDATA[pchk_start:pchk_start+4], "little", signed="False")
	if _debug: debugtrace("NKS -> PCHK start : " + str(pchk_start) + " - nb car:" + str(pchk_nbcar))
	# Unpack msgpack (JSON)
	#	- NISI
	nisi_data=VDATA[nisi_start+8:nisi_start+nisi_nbcar+4]
	debugtrace(umsgpack.unpackb(nisi_data))
	#	- NICA
	nica_data=VDATA[nica_start+8:nica_start+nica_nbcar+4]
	debugtrace(umsgpack.unpackb(nica_data))
	#	- PLID
	plid_data=VDATA[plid_start+8:plid_start+plid_nbcar+4]
	debugtrace(umsgpack.unpackb(plid_data))
	#	- PCHK
	pchk_data=VDATA[pchk_start+8:pchk_start+pchk_nbcar+4]
	debugtrace(umsgpack.unpackb(pchk_data))	
	# ----------------
	# CLOSE FILE
	VDATA.close()
	fnks.close()
	return 1

def delete_macro_NKSF(filenks):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'a+')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0
	nica_nbcar = 0
	# SEARCH NICA
	curs = VDATA.find('NICA',0) 
	curs = curs + 4	
	nica_start = curs
	nica_nbcar = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	# Delete existing Macro
	deleteFromMmap(fnks,nica_start,nica_start+nica_nbcar+4)	
	if _debug: debugtrace("NKS -> Delete Nica")
	# Construct empty NICA
	nica_data = b'\x01\x00\x00\x00\x80'
	nica_chk = struct.pack('I', len(nica_data))
	if not (nbr_pair(len(nica_data))): nica_data = nica_data + b'\x00'
	nica_data = nica_chk + nica_data
	insertIntoMmap(fnks, nica_start, nica_data)	
	if _debug: debugtrace("NKS -> INSERT  NICA LEN - srart:" + str(nica_start))
	# Update RIFF Value
	RIFF_update(fnks)
	# ----------------
	# CLOSE FILE
	sys.stdout.write(".")
	sys.stdout.flush()
	VDATA.close()
	fnks.close()
	return 1
	
	
def modify_nisi_NKSF(filenks,_name,_vendor,_author,_comment,_product,_bank,_subbank,_uuid,_vst3):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'a+')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0
	nica_nbcar = 0
	nisi_nbcar = 0
	if _debug : debugtrace("Modify tag")
	
	# SEARCH NISI
	curs = VDATA.find(b'NISI',0) 
	curs = curs + 4	
	nisi_start = curs
	nisi_nbcar = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	if _debug: debugtrace("NKS -> nb NISI car:" + str(nisi_nbcar))
	# Unpack msgpack (JSON)
	nisi_data=VDATA[curs+8:curs+nisi_nbcar+4]
	packer = umsgpack.unpackb(nisi_data)

	#Modify Data 
	if _name != "\x00":
		packer['name'] = _name.encode()
		if _debug : debugtrace("Change name : " + _name)
	if _vendor != "\x00":
		packer['vendor'] = _vendor.encode()
		if _debug : debugtrace("Change vendor : " + _vendor)
	if _author != "\x00": 
		packer['author'] = _author.encode()
		if _debug : debugtrace("Change author : " + _author)
	if _comment != "\x00": 
		packer['comment'] = _comment.encode()
		if _debug : debugtrace("Change comment : " + _comment)
	if _uuid != "\x00": 
		packer['uuid'] = _uuid.encode()
		if _debug : debugtrace("Change uuid : " + _uuid)
	if _product != "\x00": 
		packer['bankchain'][0] = _product.encode()
		if _debug : debugtrace("Change product : " + _product)
	if _bank != "\x00":
		# Clear bank
		if _bank == "" :
			i = len(packer['bankchain']) - 1
			while i > 0 :
				data_remove = packer['bankchain'].pop(i)
				if _debug : debugtrace("Remove bank&sub : " + data_remove)
				i -= 1
		else :
			if len(packer['bankchain']) <= 1 :
				packer['bankchain'].append(_bank.encode())
			else :
				packer['bankchain'][1] = _bank.encode()	
			if _debug : debugtrace("Change bank name : " + _bank)
	if _subbank != "\x00":
		# Clear subbank
		if _subbank == "" :
			i = len(packer['bankchain']) - 1
			while i > 1 :
				if _debug : debugtrace("i : " + str(i))
				data_remove = packer['bankchain'].pop(i)
				if _debug : debugtrace("Remove bank&sub : " + data_remove)
				i -= 1
		else :
			if len(packer['bankchain']) < 2 :
				debugtrace("Err. Modify Data : no bank")
			elif len(packer['bankchain']) == 3 :
				packer['bankchain'][2] = _subbank.encode()
			else : packer['bankchain'].append(_subbank.encode())
			if _debug : debugtrace("Change subbank name : " + _subbank)
	if _debug: debugtrace("NKS -> nb NISI car:" + str(nisi_nbcar))
	if _debug : debugtrace(packer)
	
	# Delete existing JSON data
	if not (nbr_pair(nisi_nbcar)) : nisi_nbcar += 1
	deleteFromMmap(fnks,nisi_start,nisi_start+nisi_nbcar+4)
	if _debug: debugtrace("NKS -> Delete Nisi")
	# Construct NISI data
	nisi_data = b'\x01\x00\x00\x00' + umsgpack.packb(packer)	
	nisi_chk = struct.pack('I', len(nisi_data))
	if not (nbr_pair(len(nisi_data))): nisi_data = nisi_data + b'\x00'
	nisi_data = nisi_chk + nisi_data
	insertIntoMmap(fnks, nisi_start, nisi_data)	
	if _debug: debugtrace("NKS -> INSERT NEW NISI LEN - srart:" + str(nisi_start))
	
	# Update RIFF Value
	RIFF_update(fnks)
	# ----------------
	# CLOSE FILE
	sys.stdout.write(".")
	sys.stdout.flush()
	VDATA.close()
	fnks.close()
	return 1

def read_vst_NKSF(filenks):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return ""
	fnks = open(filenks, 'r')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_READ)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
	curs = 0	
	# SEARCH PLID
	plid_start = VDATA.find(b'PLID',0) +4
	plid_nbcar = int.from_bytes(VDATA[plid_start:plid_start+4], "little", signed="False")
	if not (nbr_pair(plid_nbcar)) : plid_nbcar += 1
	if _debug: debugtrace("NKS -> PLID start : " + str(plid_start) + " nb car:" + str(plid_nbcar))
	data = VDATA[plid_start:plid_start+plid_nbcar+4]
	# ----------------
	# CLOSE FILE
	VDATA.close()
	fnks.close()
	return data

def import_vst_NKSF(filenks, vst_data):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'a+')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0	
	# SEARCH PLID
	plid_start = VDATA.find(b'PLID',0) + 4
	plid_nbcar = int.from_bytes(VDATA[plid_start:plid_start+4], "little", signed="False")
	if not (nbr_pair(plid_nbcar)) : plid_nbcar += 1
	if _debug: debugtrace("NKS -> PLID start : " + str(plid_start) + " nb car:" + str(plid_nbcar))
	# Delete existing PLID data
	deleteFromMmap(fnks,plid_start,plid_start+plid_nbcar+4)
	if _debug: debugtrace("NKS -> Delete Plid")
	insertIntoMmap(fnks, plid_start, vst_data)	
	if _debug: debugtrace("NKS -> INSERT NEW PLID LEN " + str(len(vst_data)) + " - srart:" + str(plid_start))
	# Update RIFF Value
	RIFF_update(fnks)
	# ----------------
	# CLOSE FILE
	sys.stdout.write(".")
	sys.stdout.flush()
	VDATA.close()
	fnks.close()
	return 1
	
def modify_plid_NKSF(filenks, _vst):
	global VDATA
	if os.stat(filenks).st_size == 0:
		if _debug: debugtrace((filenks + " is empty... arg."))
		return -1
	fnks = open(filenks, 'a+')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0
	pl_nbcar = 0
	nisi_nbcar = 0
	if _debug : debugtrace("Modify VST data")
	
	# SEARCH PLID
	curs = VDATA.find(b'PLID',0) 
	curs = curs + 4	
	plid_start = curs
	plid_nbcar = int.from_bytes(VDATA[plid_start:plid_start+4], "little", signed="False")
	if _debug: debugtrace("NKS -> PLID start : " + str(plid_start) + " nb car:" + str(nisi_nbcar))
	# Unpack msgpack (JSON)
	plid_data=VDATA[plid_start+8:plid_start+nisi_nbcar+4]
	packer = umsgpack.unpackb(plid_data)
	plid_data = _vst

def export_map_NI(fileToExport, fileMap):
	global VDATA
	fnks =  open(fileToExport, 'rb')
	fmap = open(fileMap, "wb")
# ------- Patch WINDOWS v2.8C
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_READ)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_READ)
	curs = 0
	nks_nbcar = 0
	nks_index = 0
	# Search DSIN
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1)
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	nks_index = curs
	curs = VDATA.find(b'\x44\x53\x49\x4E\x74\x00\x00\x00',curs+1) 
	nks_nbcar = curs - nks_index	
	if _debug: debugtrace("NKS Index:" + str(nks_index))
	if _debug: debugtrace("nb car NKS:" + str(nks_nbcar))
	nks_data=VDATA[nks_index:nks_index + nks_nbcar]
	fmap.write(nks_data)
	sys.stdout.write("*")
	# ----------------
	# CLOSE FILE
	sys.stdout.flush()
	VDATA.close()
	fmap.close()
	fnks.close()
	return 1

def import_map_NI(fileToChange, fileMap):
	global VDATA
	if fileMap == "" :
		# Filemap is empty, delete map...
		data = b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00\x94\x39\x8D\xD4\x3C\xD6\x45\x05\x82\xCD\x41\xB0\x1E\x56\xC6\xB1\x38\x00\x00\x00\x00\x00\x00\x00\x44\x53\x49\x4E\x79\x00\x00\x00\x01\x00\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x44\x53\x49\x4E\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00'
	else :
		# Read NKS Map
		if os.stat(fileMap).st_size == 0: 
			debugtrace((fileMap + " is empty... arg."))
			return -1
		fmap = open(fileMap , 'rb')
		data = fmap.read()
		if _debug: debugtrace("MAP -> Read Map Data")
	
	if os.stat(fileToChange).st_size == 0:
		debugtrace((fileToChange + " is empty... arg."))
		return -1
	fnks =  open(fileToChange, 'a+')
	if _debug: debugtrace("Your plateform " + platform.system())
	if (platform.system() == "Windows") : VDATA = mmap.mmap(fnks.fileno(),0, access=mmap.ACCESS_WRITE)
	else : VDATA = mmap.mmap(fnks.fileno(),0, mmap.MAP_SHARED, mmap.ACCESS_WRITE)
	curs = 0
	nks_nbcar = 0
	if _debug : debugtrace("Remplace map")
	# Search hsin
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1)
	curs = VDATA.find(b'\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00',curs+1) 
	nks_index = curs
	curs = VDATA.find(b'\x44\x53\x49\x4E\x74\x00\x00\x00',curs+1) 
	nks_nbcar = curs - nks_index	
	if _debug : debugtrace("NKS Index:" + str(nks_index))
	if _debug : debugtrace("nb car NKS:" + str(nks_nbcar))
	if nks_nbcar > 0:
		deleteFromMmap(fnks,nks_index,nks_index+nks_nbcar)
		if _debug : debugtrace("NKS -> Delete MAP")
		if len(data) > 0 :
			insertIntoMmap(fnks, nks_index, data)
			if _debug : debugtrace("NKS -> Insert Map Data (" + str(len(data)) + " car) start at " + str(nks_index))
		else: debugtrace("ERROR : MAP -> File empty")
	else :
		debugtrace("ERROR : DSIN in file " + fileToChange)
	# Correct len file header
	AddSizeOfFile(fnks)
	
	sys.stdout.write("*")
	# ----------------
	# CLOSE FILE
	sys.stdout.flush()
	VDATA.close()
	if not(fileMap == ""): fmap.close()
	fnks.close()
	return 1
	
	
def change_file(file,name,vendor,author,comment,product,bank,subbank,readinfo,delete_macro,forceBankID,massiveDataCorrection,DataNICorrection,listtag):
	global VDATA
	f = open(file, 'a+')
	VDATA = mmap.mmap(f.fileno(), 0)
	deletebank = 0
	# Go Native DATA header
	#hsin = b'\x00\x00\x00\x00\x01\x00\x00\x00hsin\x01\x00\x00\x00\x00\x00\x00\x00'
	hsin = b'\x00\x00\x00\x00\x01\x00\x00\x00\x68\x73\x69\x6E\x01\x00\x00\x00\x00\x00\x00\x00'
	hsin_length = 36
	DSIN_length = 20
	if VDATA[4:4+20] != hsin :
		if _debug : debugtrace(VDATA[4:4+20])
		if _debug : debugtrace(hsin)

		return -1 
	curs = hsin_length + 4
	for i in range(2): 
		data_length = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
		curs = curs + 4 + DSIN_length + data_length + hsin_length
	dataNI_pstart = curs
	# Force Correct Data_NI length header information
	if DataNICorrection :
		dataNI_pend = VDATA.find(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00DSINy\x00\x00\x00',dataNI_pstart)
		if dataNI_pend < (dataNI_pstart) :
			if not _debug : debugtrace("File:" + file)
			debugtrace("Data NI Correction -> NOT POSSIBLE")
			if _debug : debugtrace("start:" + str(dataNI_pstart) + " end:" + str(dataNI_pend))
		else :
			if _debug : debugtrace("Data NI Correction")
			if _debug : debugtrace("start:" + str(dataNI_pstart) + " end:" + str(dataNI_pend))
			dataNI_length = (dataNI_pend) - (dataNI_pstart)
	else : 
		dataNI_length = int.from_bytes(VDATA[curs:curs+4], "little", signed="False")
	dataNI = VDATA[dataNI_pstart:dataNI_pstart+dataNI_length]
	if _debug : debugtrace("dataNI_pstart:" + str(dataNI_pstart) + " - dataNI_length:" + str(dataNI_length))
	curs = 60
	
	name_pindex = curs
	name_pstart = name_pindex + 4
	name_nbrcar = int.from_bytes(dataNI[name_pindex:name_pindex+4], "little", signed="False")
	if _debug : debugtrace("NAME curs:" + str(curs) + " - nbcar:" + str(name_nbrcar))
	if name_nbrcar < 0 : return -1
	curs = name_pstart + (name_nbrcar*2)
	
	author_pindex = curs 
	author_pstart = author_pindex + 4
	author_nbrcar = int.from_bytes(dataNI[author_pindex:author_pindex+4], "little", signed="False")
	if _debug : debugtrace("AUTHOR curs:" + str(curs)  + " - nbcar:" + str(author_nbrcar))
	curs = author_pstart + (author_nbrcar*2)
	
	vendor_pindex = curs
	vendor_pstart = vendor_pindex + 4
	vendor_nbrcar = int.from_bytes(dataNI[vendor_pindex:vendor_pindex+4], "little", signed="False")
	if _debug : debugtrace("VENDOR curs:" + str(curs) + " - nbcar:" + str(vendor_nbrcar))
	curs = vendor_pstart + (vendor_nbrcar*2)
	
	comment_pindex = curs 
	comment_pstart = comment_pindex + 4
	comment_nbrcar = int.from_bytes(dataNI[comment_pindex:comment_pindex+4], "little", signed="False")
	if _debug : debugtrace("COMMENT curs:" + str(curs) + " - nbcar:" + str(comment_nbrcar))
	curs = comment_pstart + (comment_nbrcar*2)
	curs = curs + 36
	
	bankid_pstart = curs
	if _debug : debugtrace("BANKID curs:" + str(bankid_pstart))
	bankid = dataNI[bankid_pstart:bankid_pstart+1]
	if bankid == b'\x02':
		isbank=1
		issubbank=0
		if _debug : debugtrace("bankid:x02 (just bank)")
	elif bankid == b'\x03':
		isbank=1
		issubbank=1
		if _debug : debugtrace("bankid:x03 (bank and sub-bank)")
	else : # bankid = \x01
		isbank=0
		issubbank=0
		if _debug : debugtrace("bankid:No bank and sub-bank")
	curs = curs + 4

	product_pindex = curs
	product_pstart = product_pindex + 4
	product_nbrcar = int.from_bytes(dataNI[product_pindex:product_pindex+4], "little", signed="False")
	if _debug : debugtrace("PRODUCT curs:" + str(product_pindex) + " nbcar:" + str(product_nbrcar))
	curs = product_pstart + (product_nbrcar * 2)	
	
	bank_pindex = curs
	if isbank:
		bank_pstart = bank_pindex + 4
		bank_nbrcar = int.from_bytes(dataNI[bank_pindex:bank_pindex+4], "little", signed="False")
		if _debug : debugtrace("BANK curs:" + str(bank_pindex) + " nbcar:" + str(bank_nbrcar))
		curs = bank_pstart + (bank_nbrcar * 2)

	subbank_pindex = curs
	if issubbank:
		subbank_pstart = subbank_pindex + 4
		subbank_nbrcar = int.from_bytes(dataNI[subbank_pindex:subbank_pindex+4], "little", signed="False")
		if _debug : debugtrace("SUBBANK curs:" + str(subbank_pindex) + " nbcar:" + str(subbank_nbrcar))
		curs = subbank_pstart + (subbank_nbrcar * 2)
	
#	tagnbr_pstart = curs
#	if _debug : debugtrace("TagNbr curs:" + str(tagnbr_pstart))
#	tagnbr = struct.unpack('h', VDATA[tagnbr_pstart:tagnbr_pstart+2])[0]
#	if _debug : debugtrace("Number of tag:" + str(tagnbr))
#	i = 0
#	tag_pstart = []
#	tag_nbrcar = []
#	tag = []
#	tag_pindex = curs + 4
#	while i < tagnbr :
#		tag_pstart.insert(i,  tag_pindex + 4)
#		tag_nbrcar.insert(i, struct.unpack('h', VDATA[tag_pindex:tag_pindex+2])[0] )
#		if _debug : debugtrace("Tag " + str(i+1) + " curs:" + str(tag_pstart[i]) + " nbcar:" + str(tag_nbrcar[i]))
#		tag_pindex = tag_pstart[i] + (tag_nbrcar[i] * 2)
#		tag.insert(i, VDATA[tag_pstart[i]:tag_pstart[i]+(tag_nbrcar[i]*2)].decode('utf-16', 'replace'))
#		i += 1		
#	if _debug : debugtrace(" ")
	
	# -----------------
	# READ & PRINT DATA
	if readinfo != "":
		name=dataNI[name_pstart:name_pstart+(name_nbrcar*2)].decode('utf-16', 'replace')
		author=dataNI[author_pstart:author_pstart+(author_nbrcar*2)].decode('utf-16', 'replace')
		vendor=dataNI[vendor_pstart:vendor_pstart+(vendor_nbrcar*2)].decode('utf-16', 'replace')
		product=dataNI[product_pstart:product_pstart+(product_nbrcar*2)].decode('utf-16', 'replace')
		if isbank :	bank=dataNI[bank_pstart:bank_pstart+(bank_nbrcar*2)].decode('utf-16', 'replace')
		else : bank = "-"
		if issubbank: subbank=dataNI[subbank_pstart:subbank_pstart+(subbank_nbrcar*2)].decode('utf-16', 'replace')
		else : subbank = "-"
		comment=dataNI[comment_pstart:comment_pstart+(comment_nbrcar*2)].decode('utf-16', 'replace')
#		print name + ";" + author + ";" + vendor + ";" + product + ";" + bank + ";" + subbank + ";" + comment
		if readinfo == "default" :
			print("Name: " + name + " | Author: " + author + " | Vendor: " + vendor)
			print("Product: " + product + " | Bank: " + bank + " | Subbank: " + subbank)
#			for i, elt in enumerate(tag):
#				print("Tag{}: {}".format(i, elt))
			print ("--")
		if readinfo == "csv" :
			print(file + ";" + name + ";" + author + ";" + vendor + ";" + product + ";" + bank + ";" + subbank)
		if readinfo == "xml" :
			print("\t<NI_File>")
			print("\t\t<filename>" + file + "</filename>")
			print("\t\t<name>" + name + "</name>")
			print("\t\t<author>" + author + "</author>")
			print("\t\t<vendor>" + vendor + "</vendor>")
			print("\t\t<product>" + product + "</product>")
			print("\t\t<bank>" + bank + "</bank>")
			print("\t\t<subbank>" + subbank + "</subbank>")
			print("\t\t<comment>" + comment + "</comment>")
			for i, elt in enumerate(tag):
				print("\t\t<tag>" + elt + "</tag>")
			print("\t</NI_File>")
		

	# ----------------
	# MODIFY DATA
	else :
		
		# Massive - delete macro
		if delete_macro:
			macro_pstart = VDATA.find(b'\x44\x53\x49\x4E\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00',0) 
			macro_pend = VDATA.find(b'\x44\x53\x49\x4E\x74\x00\x00\x00',0) 
			if _debug : debugtrace("macro begin:" + str(macro_pstart) + " macro end:" + str(macro_pend))
			if macro_pstart > 0 and macro_pend > 0:
				macro_nbcar = macro_pend - macro_pstart
				deleteFromMmap(f, macro_pstart, macro_pend)
				if _debug : debugtrace("Delete macro define")
				data = b'\x44\x53\x49\x4E\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00'
				insertIntoMmap(f,macro_pstart, data)
				if _debug : debugtrace("Insert Blank macro")
			else : debugtrace("Unable to delete Macro. file :" + shortFile(file))
		
		# Bank test and Subbank interaction
		if bank == "" :
			isnewbank = 0
			# If Bank delete, delete subbank
			if issubbank:
				subbank = ""
		elif bank == "\x00" :
			isnewbank = isbank
		else : isnewbank = 1
			
		# Subbank
		if subbank != "\x00":
			if isnewbank or isbank:
				if issubbank:
					# delete existing subbank
						if _debug : debugtrace("subbank delete start:" + str(subbank_pindex) + " len:" + str(subbank_nbrcar*2+4))
						dataNI=dataNI[:subbank_pindex]+dataNI[subbank_pindex+(subbank_nbrcar*2)+4:]
				# subbank delete
				if subbank == "":
						issubbank = 0
						
				# insert or modify subbank 
				elif bank != "" :
					data = data_format(subbank)
					if _debug : debugtrace("subbank insert at:" + str(subbank_pindex) + " len:" + str(len(data)))
					dataNI=dataNI[:subbank_pindex] + data + dataNI[subbank_pindex:]
					issubbank = 1
			else :
				debugtrace("Sub-bank not Add. Add bank to add sub-bank. file :" + shortFile(file))
				issubbank = 0
		# Bank
		if bank != "\x00":
			if isbank:
				# delete existing bank
				if _debug : debugtrace("bank delete start:" + str(bank_pindex) + " len:" + str(bank_nbrcar*2+4))
				if _debug : debugtrace("bank_nbrcar:" + str(bank_nbrcar))
				dataNI=dataNI[:bank_pindex] + dataNI[bank_pindex+(bank_nbrcar*2)+4:]
			# Bank delete : Modify bankID 
			if bank == "" :
				isbank = 0
			# insert or modify bank 
			else :
				data = data_format(bank)
				if _debug : debugtrace("bank insert at:" + str(bank_pindex) + " len:" + str(len(data)))
				dataNI=dataNI[:bank_pindex] + data + dataNI[bank_pindex:]
				isbank = 1
		# Product Update
		if product != "\x00" and product != "":
			data = data_format(product)
			if _debug : debugtrace("PRODUCT update start:" + str(product_pindex) + " len:" + str(product_nbrcar*2+4))
			dataNI=dataNI[:product_pindex] + data + dataNI[product_pindex+(product_nbrcar*2)+4:]
		
		# If Force BankID activate
		if forceBankID != "":
			bank = "" # Force BankId Modification
			if forceBankID == "b": 
				isbank = 1
				issubbank = 0
				if _debug : debugtrace("Force ID = Bank")
			elif forceBankID == "s": 
				isbank = 1
				issubbank = 1	
				if _debug : debugtrace("Force ID = Bank AND Subbank")
			else : 
				isbank = 0
				issubbank = 0
				if _debug : debugtrace("Force ID = no Bank, no Subbank")
				
		# Modification BankID
		if bank != "\x00" or subbank != "\x00":
			oldid = bankid
			if (isbank and issubbank): bankid = b'\x03'
			elif (isbank and (not issubbank)): bankid = b'\x02'
			else : bankid = b'\x01'
			dataNI = dataNI[:bankid_pstart] + bankid + dataNI[bankid_pstart+1:]
			if _debug : debugtrace("BANKID Update")
			
		# Massive Data Correction
		if massiveDataCorrection :			
			massiveDC_pend = bankid_pstart - 1
			massiveDC_pstart = massiveDC_pend - 44
			if massiveDC_pstart > 0 and massiveDC_pend > 0:
				massiveDC_nbcar = massiveDC_pend - massiveDC_pstart
				# data = b'\xff\xff'
				data = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\xB0\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00'
				if _debug : debugtrace("Massive Data Correction update:" + str(massiveDC_pstart) + " end:" + str(massiveDC_pend))
				dataNI=dataNI[:massiveDC_pstart] + data + dataNI[massiveDC_pend:]
			
		# Comment Update
		if comment != "\x00":
			data = data_format(comment)
			if _debug : debugtrace("Comment update at:" + str(comment_pindex) + " len:" + str(comment_nbrcar*2)+4)
			dataNI=dataNI[:comment_pindex] + data + dataNI[comment_pindex+comment_nbrcar*2+4:]

		# Vendor Update
		if vendor != "\x00":
			data = data_format(vendor)
			if _debug : debugtrace("Vendor update at:" + str(vendor_pindex) + " len:" + str(vendor_nbrcar*2+4))
			dataNI=dataNI[:vendor_pindex] + data + dataNI[vendor_pindex+vendor_nbrcar*2+4:]

		# Author Update
		if author != "\x00":
			data = data_format(author)
			if _debug : debugtrace("Author update at:" + str(author_pindex) + " len:" + str(author_nbrcar*2+4))
			dataNI=dataNI[:author_pindex] + data + dataNI[author_pindex+author_nbrcar*2+4:]

		# Name Update
		if name != "\x00" and name != "":
			data = data_format(name)
			if _debug : debugtrace("Name update at:" + str(name_pindex) + " len:" + str(name_nbrcar*2+4))
			dataNI=dataNI[:name_pindex] + data + dataNI[name_pindex+name_nbrcar*2+4:]

		# Tag --AT Work--
		if len(listtag[1]) > 0:
			if _debug : debugtrace("Tag to modify")
			stag = []
			for t in listtag: 
				if t[0] == '-' : # delete tag
					print(t[1][1])
					print(tag)
					if t[1] in tag :
						tag.remove(t[1])
						
				if t[0] == '+' : # add tag
					stag = t[1].split("\:") # search if root tag to add
					newtag = ""
					if len(stag) > 1:
						for i in range(1, len(stag) -1):
							newtag = newtag + "\:" + stag[i]
							if _debug : debugtrace("New tag :" + newtag)
							listtag[0].append("+")
							listtag[1].append(newtag)
				if t in tag :
					print("Tag " + t + " est deja la")
				else : print("Tag " + t + " non present")
				
		# delete existing data_NI
		if _debug : debugtrace("dataNI delete start:" + str(dataNI_pstart) + " len:" + str(dataNI_length))
		deleteFromMmap(f,dataNI_pstart, dataNI_pstart+(dataNI_length))
		# insert data_NI Updated
		dataNI_length = len(dataNI)
		size_dataNI = struct.pack('<I', dataNI_length)
		dataNI = size_dataNI + dataNI[4:]
		if _debug : debugtrace("dataNI insert at:" + str(dataNI_pstart) + " len:" + str(dataNI_length))
		insertIntoMmap(f,dataNI_pstart, dataNI)
		
		# Correct length file header information (4 first bytes)
		AddSizeOfFile(f)
		
	# ----------------
	# CLOSE FILE
	sys.stdout.flush()
	VDATA.close()
	f.close()
	return 1

def shortusage():
	print(sys.argv[0] + " v" + __version__ + " - Odie Research.")
	print("Use '" + sys.argv[0] + " -h' for help")
	
def usage():
	print(sys.argv[0] + " is a tool to modify the product name and to add, remove or modify the bank name for Native Instruments files (.mxprj .mxgrp .mxsnd .nmsv .nrkt .nki .nkm .nksn .mxfx .nfm8 .nbkt).")
	print("You agree that you are using this software solely at your awn risk. Company provides the software \"as is\" and without warranty of any kind.")
	print(" ")
	print(sys.argv[0] + " [-d] [-n name] [-a author] [-v vendor] [-c comment] [-p product] [-b bank] [-s subbank]|[-l|--list [xml|csv]] [-r] filenames")
	print("-l | --list      : list all information (no modification)")
	print("--list [xml|csv] : list all information and output to specific format")
	print("-n | --name      : modify name field")
	print("-a | --author    : add/modify/clear author field")
	print("-v | --vendor    : add/modify/clear vendor field")
	print("-c | --comment   : add/modify/clear comment field")
	print("-u | --uuid      : add/modify/clear uuid field for nksf or nksfx file")
	print("-p | --product   : modify product")
	print("-b | --bank      : add/modify/clear bank (-b \"\" -> clear bank)")
	print("-s | --subbank   : add/modify/clear sub-bank (-s \"\" -> clear sub-bank)")
#	print("-t | --tag       : add/modify/clear tag" // Dev. in Progress)
	print("-e | --export    : export NKS Map Data from nki, nmsv or nksn to file.map")
	print("-i | --import    : import file.map (NKS Map) to nki, nmsv or nksn file")
	print("                   (After modify, do a Kontakt batch resave) - if no file.map, delete NKS Data")
	print("-m | --make      : create nks file from VST patch (snapshot)")
	print("                   (delete offset byte before import patch)")
	print("--clearmacro     : clear Macro for Massive and NKS files only ")
	print("                   (some macro information is no good for Maschine)")
	print("--forceBankID    : [bank|bankANDsub] just force the ID Modification. [b/s]")
	print("                   **WARNING** This option can corrupt your files")
	print("--niheaderCorrect: Correct file modify with this tool under v4 version")
	print("                   **WARNING** This option can corrupt your files")
	print("--massiveCorrect : Correct corrupt Data in massive file. ")
	print("                   **WARNING** This option can corrupt your files")
	print("-d : mode debug")
	print("-V : verbose mode (print information but no debug information)")
	print("-r | --recursive : Recursive mode in directory")
	print(" ")
	print("version : " + __version__ + " - Odie Research")

def main(argv) :
	try:
		opts, args = getopt.getopt(argv, "hdVlr:n:a:v:c:u:p:b:s:t:e:i:m:", ["help", "list=", "name=", "author=", "vendor=", "comment=", "uuid=", "product=", "bank=", "author=", "subbank", "tag=", "clearmacro", "massiveCorrect", "niheaderCorrect","forceBankID=", "export=", "import=", "make=", "recursive=", "vst="])
	except getopt.GetoptError :
		print("F**k, an Error in arg")
		sys.exit(2)
	if len(sys.argv) <= 1 : 
		shortusage()
		sys.exit()
	# INIT default data (\x00 = no modifiaction)
	name = "\x00"
	vendor = "\x00"
	author = "\x00"
	comment = "\x00"
	product = "\x00"
	bank = "\x00"
	subbank = "\x00"
	author = "\x00"
	uuid = "\x00"
	vst = False
	vst3 = {'modify': False, 'name': "", 'vendor': "", 'uid1': 0, 'uid2': 0, 'uid3': 0, 'uid4':0}
	listtag = [[] for i in range(2)]
	readinfo = ""
	forceBankID = ""
	recursive_dir = ""
	delete_macro = 0
	massiveDataCorrection = 0
	DataNICorrection = 0
	nks_map = ""
	impexp = 0
	create_patch = False
	patch_offset = 0
	
	for opt, arg in opts :
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt == '-d':
			global _debug 
			_debug = 1
		elif opt == '-V':
			global _verbose 
			_verbose = 1
		elif opt in ("-l"):
			readinfo = "default"
			if _debug : debugtrace("Read Information")
		elif opt in ("--list"):
			readinfo = arg
			if _debug : debugtrace("Read Information and output to " + arg)
		elif opt in ("-n", "--name"):
			name = arg
			if _debug : debugtrace("Add/Modify name:" + arg)
		elif opt in ("-a", "--author"):
			author = arg
			if _debug : debugtrace("Add/Modify author:" + arg)
		elif opt in ("-v", "--vendor"):
			vendor = arg
			if _debug : debugtrace("Add/Modify vendor:" + arg)
		elif opt in ("-c", "--comment"):
			comment = arg
			if _debug : debugtrace("Add/Modify comment:" + arg)
		elif opt in ("-b", "--bank"):
			bank = arg
			if _debug : debugtrace("Add/Modify bank name:" + arg)
		elif opt in ("-s", "--subbank"):
			subbank = arg
			if _debug : debugtrace("Add/Modify subbank name:" + arg)
		elif opt in ("-p", "--product"):
			product = arg
			if _debug : debugtrace("Modify product name:" + arg)
		elif opt in ("-u", "--uuid"):
			uuid = arg
			if _debug : debugtrace("Modify uuid:" + arg)
		elif opt in ("-t", "--tag"):
			listtag[0].append(arg[0])
			listtag[1].append(arg[1:])
			if _debug : debugtrace("Add/Delete tag:" + arg)
		elif opt in ("--clearmacro"):
			delete_macro = 1
			if _debug : debugtrace("Delete Macro")
		elif opt in ("-i", "--import"):
			impexp = 1
			nks_map = arg
			if _debug : debugtrace("Import nks map from :" + nks_map)
		elif opt in ("-e", "--export"):
			impexp = 2
			nks_map = arg
			if _debug : debugtrace("Export nks map to :" + nks_map)
		elif opt in ("--forceBankID"):
			forceBankID = arg
			if _debug : debugtrace("Force BankID Modification")
		elif opt in ("-m", "--make"):
			create_patch = True
			patch_offset = arg
			if _debug : debugtrace("Create nksf file")
		elif opt in ("--massiveCorrect"):
			massiveDataCorrection = 1
			if _debug : debugtrace("Force Massive Data Correction")
		elif opt in ("--niheaderCorrect"):
			DataNICorrection =1
			if _debug : debugtrace("Force DATA NI header Correction")
		elif opt in ("--vst"):
			vst = True
			filesource = arg
			if _debug : debugtrace("VST modification")
		elif opt in ("-r", "--recursive"):
			recursive_dir = arg
			if _debug : debugtrace("Recusrive Mode:" + recursive_dir)
		elif opt in ("--vst3-name"):
			vst3['modify'] = True
			vst3['name'] = arg
			if _debug : debugtrace("VST3 modify")
		elif opt in ("--vst3-vendor"):
			vst3['modify'] = True
			vst3['vendor'] = arg
			if _debug : debugtrace("VST3 modify")		
		elif opt in ("--vst3-uid1"):
			vst3['modify'] = True
			vst3['uid1'] = arg
			if _debug : debugtrace("VST3 modify")
		elif opt in ("--vst3-uid2"):
			vst3['modify'] = True
			vst3['uid2'] = arg
			if _debug : debugtrace("VST3 modify")
		elif opt in ("--vst3-uid3"):
			vst3['modify'] = True
			vst3['uid3'] = arg
			if _debug : debugtrace("VST3 modify")
		elif opt in ("--vst3-uid4"):
			vst3['modify'] = True
			vst3['uid4'] = arg
			if _debug : debugtrace("VST3 modify")		

	# if readinfo : print "Name;Author;Vendor;Product;Bank;SubBank;Comment\r"
	if readinfo == "xml": print("<library>")
	# Test VST extract data... --WORKS IN PROGRESS--
	if vst :
		if _debug : debugtrace("Read VST data from " + filesource)
		file_ext = os.path.splitext(filesource)[1]
		if file_ext in (".nksf", ".nksfx"):
			vst_data = read_vst_NKSF(filesource)
	# No -r option
	if recursive_dir == "":
		for filename in args:
			if not os.path.isfile(filename) :
				print(color.ERROR + "File ERROR" + color.FILE + " " + filename + color.END + " is not a file...")
				sys.exit(-1)
			if _debug:
				print("--")
				print(filename)
			file_ext = os.path.splitext(filename)[1]
			file_short = os.path.basename(filename)
			if create_patch :
				if (file_ext != ".nksf") and (file_ext != ".nksfx"):
					if _debug : debugtrace("Create NKS File with " + filename)
					filename = create_NKSF(filename, patch_offset, "i")
					if filename == -1: print("Error to create nks file")
					else :
						namehead, nametail = os.path.split(filename)
						name = os.path.splitext(nametail)[0]
			if file_ext in (".nksf", ".nksfx"):
				# Read info.
				if readinfo == "default": list_nisi_NKSF(filename)
				elif vst :
					if _debug : debugtrace("Modify VST data from " + filename)
					if import_vst_NKSF(filename, vst_data) < 0 :
						print("ERROR VST Modz : " + filename)
					sys.stdout.write("*")
				else :
					# Import  NKS Data
					if impexp == 1: import_map_NKSF(filename, nks_map)
					# Export  NKS Data
					elif impexp == 2: export_map_NKSF(filename, nks_map)
					# Other actions
					if modify_nisi_NKSF(filename,name,vendor,author,comment,product,bank,subbank,uuid,vst3) < 0 :
						print(color.FILE + file_short + color.ERROR + "ERROR")
					elif _verbose : print(color.FILE + file_short + color.OK + "OK")
					else : print(".")
					sys.stdout.write("*")
			elif file_ext in (".mxprj", ".mxgrp", ".mxsnd", ".nmsv", ".nrkt", ".nki", ".nkm", ".nksn", ".mxfx", ".nfm8", ".nbkt"):
				if impexp > 0:
				# Import Export NKS Data
					if file_ext in (".nksn", ".nki", ".nmsv"):
						if impexp == 1:
							# Import
							import_map_NI(filename, nks_map)
						else :
							# Export
							export_map_NI(filename, nks_map)
					else :
					    if _debug : debugtrace(color.BOLD + "File not supported..." + color.END)
				# Other actions
				#if file_ext == ".nmsv" and product != "\x00":
				#	if _debug : debugtrace("Massive File : Don't Modified product name"
				#	product = "\x00"
				if file_ext != ".nmsv":
					massiveDataCorrection = 0
				if change_file(filename,name,vendor,author,comment,product,bank,subbank,readinfo,delete_macro,forceBankID,massiveDataCorrection,DataNICorrection,listtag) < 0 :
					print('{0:<80} {1:>5}'.format(color.FILE + file_short, color.EROOR + "ERROR" + color.END))
				elif _verbose : print('{0:<80} {1:>5}'.format(color.FILE + file_short, color.OK + "OK" + color.END))
				else : sys.stdout.write(".")
	# -r option // Recusrsive mode
	else:
		if not os.path.isdir(recursive_dir) :
			print(color.ERROR + "FOLDER ERROR" + color.FILE + " " + recursive_dir + color.END + " is not a folder...")
			sys.exit(-1)			
		for root, dirs, files in os.walk(recursive_dir):
			for fname in files:
				filename = os.path.join(root, fname)
				if not os.path.isfile(filename) :
					print(color.ERROR + "File ERROR" + color.FILE + " " + filename + color.END + " is not a file...")
					sys.exit(-1)
				file_ext = os.path.splitext(filename)[1]
				file_short = os.path.basename(filename)
				if create_patch :
					if fname[0] != '.' :
						if _debug : debugtrace("Create NKS File with " + filename)
						filename = create_NKSF(filename, patch_offset, "i")
						if filename == -1: print("Error to create nks file")
						else :
							namehead, nametail = os.path.split(filename)
							name = os.path.splitext(nametail)[0]
				if file_ext in (".nksf", ".nksfx"):
					# Read info.
					if readinfo == "default": list_nisi_NKSF(filename)
					elif vst :
						if _debug : debugtrace("Modify VST data from " + filename)
						if import_vst_NKSF(filename, vst_data) < 0 :
							print("ERROR VST Modz : " + filename)
						sys.stdout.write("*")
					else :
						# Import  NKS Data
						if impexp == 1: import_map_NKSF(filename, nks_map)
						# Export  NKS Data
						elif impexp == 2: export_map_NKSF(filename, nks_map)
						# Other actions
						if modify_nisi_NKSF(filename,name,vendor,author,comment,product,bank,subbank,uuid,vst3) < 0 :
							print(color.FILE + file_short + color.ERROR + "ERROR")
						elif _verbose : print(color.FILE + file_short + color.OK + "OK")
						else : print(".")
						sys.stdout.write("*")
				elif file_ext in (".mxprj", ".mxgrp", ".mxsnd", ".nmsv", ".nrkt", ".nki", ".nkm", ".nksn", ".mxfx", ".nfm8", ".nbkt"):
					if _debug:
						debugtrace("--")
						debugtrace(filename)
					if impexp > 0:
					# Import Export NKS Data
						if file_ext in (".nksn", ".nki", ".nmsv"):
							if impexp == 1:
								# Import
								import_map_NI(filename, nks_map)
							else :
								# Export
								export_map_NI(filename, nks_map)
						else :
						    if _debug : debugtrace("File not supported...")
					# Other actions
					if file_ext == ".nmsv" and product != "\x00":
						if _debug : debugtrace("Massive File : Don't Modified product fname")
						product = "\x00"
					if file_ext != ".nmsv":
						massiveDataCorrection = 0
					if change_file(filename,name,vendor,author,comment,product,bank,subbank,readinfo,delete_macro,forceBankID,massiveDataCorrection,DataNICorrection,listtag) < 0 :
						print('{0:<80} {1:>5}'.format(color.FILE + file_short, color.EROOR + "ERROR" + color.END))
					elif _verbose : print('{0:<80} {1:>5}'.format(color.FILE + file_short, color.OK + "OK" + color.END))
					else : sys.stdout.write(".")
	if readinfo == "xml": print("</library>")
	print(" ")

if __name__ == "__main__":
	main(sys.argv[1:])