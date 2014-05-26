# -*- coding: iso-8859-15 -*-
'''
#==============================================================================
CSV_creator_full
@author: aelshen, steele42
#==============================================================================
'''

import os
import sys
import re
from codecs import open as codec_open

#==============================================================================
#--------------------------------Constants-------------------------------------
#==============================================================================
LABELS = '''
         id transcription url
         '''
TRANSCRIPTION_PATH = os.getcwd() + '/Transcription'
video_list = open('vid_list', 'r').readlines()

#==============================================================================
#-----------------------------------Main---------------------------------------
#==============================================================================
def main():
	output_file = sys.argv[1]

	transcriptions_list = []

	for transcription in os.listdir(TRANSCRIPTION_PATH):
		vid_id = re.search(r'_([0-9]+)\.txt', transcription).groups()[0]
		vid_youtube_id = re.search(r'watch\?v=(.+)&?', video_list[ int(vid_id) - 1 ]).groups()[0]

		file = open( os.path.join(TRANSCRIPTION_PATH, transcription) ).readlines()
		text = '"'
		for line in file:
			line = line.strip()
			if (len(line) > 0) and (line[0] != '#') and (line[0] != '<'):
				text += line.replace('\n', '').replace('"', "'").strip() + '<br>'
		text += '"'
		transcriptions_list.append(Row(vid_id, text, vid_youtube_id))

	MakeCSV(transcriptions_list, output_file)

	print("CSV file created successfully!")

##-------------------------------------------------------------------------
## MakeCSV()
##-------------------------------------------------------------------------
##    Description:    Create a CSV file with the data
##
##    Arguments:      Rows; list of Row objects
##					  out; output filename
##
##    Called By:      main()
##-------------------------------------------------------------------------
def MakeCSV(transcriptions_list, out):

	with codec_open(out, 'w', 'utf-8-sig') as outfile:
		outfile.write(','.join(LABELS.split()) + os.linesep)
		for x in transcriptions_list:
			outfile.write(x.comma_delimited + os.linesep)


#==============================================================================    
#----------------------------------Classes-------------------------------------
#==============================================================================
##-------------------------------------------------------------------------
## Class Classname
##-------------------------------------------------------------------------
##    Description:    A container class to hold info for each video
##
##    Arguments:      transcription; a list of strings from a file.readlines() call
##
##    Properties:    self.info; list of all relevant info for each row in the CSV
##                   self.comma_delimited; string representation of self.info
##
##-------------------------------------------------------------------------
class Row:
    def __init__(self, id, text, yt_id):
        self.info = [id, text, yt_id]
        self.comma_delimited = ",".join(self.info)
    
    def __repr__(self):
        return self.comma_delimited

if __name__ == "__main__":
    sys.exit( main() )