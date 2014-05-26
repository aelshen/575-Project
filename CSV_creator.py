# -*- coding: iso-8859-15 -*-
'''
#==============================================================================
CSV_creator
@author: aelshen, steele42
#==============================================================================
'''

import os
import sys
import re
import random
from codecs import open as codec_open

#==============================================================================
#--------------------------------Constants-------------------------------------
#==============================================================================
DEBUG = True
LABELS = '''
         chunk_1_id    chunk_1_start    chunk_1_end    chunk_1_text    chunk_1_url    chunk_2_id    chunk_2_start    chunk_2_end    chunk_2_text    chunk_2_url    chunk_3_id    chunk_3_start    chunk_3_end    chunk_3_text    chunk_3_url    chunk_4_id    chunk_4_start    chunk_4_end    chunk_4_text    chunk_4_url    chunk_5_id    chunk_5_start    chunk_5_end    chunk_5_text    chunk_5_url
         ''' 
OUTFILE = '575_HIT.csv'     
TRANSCRIPTION_PATH = os.getcwd() + '/Transcription'     
video_list = open('vid_list', 'r').readlines()

#==============================================================================
#-----------------------------------Main---------------------------------------
#==============================================================================
def main():
    transcriptions_list = []
    
    for transcription in os.listdir(TRANSCRIPTION_PATH):
        vid_id = re.search(r'_([0-9]+)\.txt', transcription).groups()[0]
        vid_youtube_id = re.search(r'watch\?v=(.+)&?', video_list[ int(vid_id) - 1 ]).groups()[0].strip()
        
        
        file = open( os.path.join(TRANSCRIPTION_PATH, transcription) ).readlines()
        
        cur_chunk = 0
        new_chunk = False
        start_time = ''
        end_time = ''
        text = ''
        
        for line in file:
            m = re.search(r'^#([0-9:]*)#', line)
            if m:
                if not new_chunk:
                    new_chunk = True
                    start_time = GetTimestamp( m.groups()[0] )
                else:
                    new_chunk = False
                    cur_chunk += 1
                    end_time = GetTimestamp( m.groups()[0] )
                    
                    cur_id = vid_id + '.' + str(cur_chunk)
                    temp = Chunk(cur_id, start_time, end_time, text, vid_youtube_id)
                    
                    
                    transcriptions_list.append(temp)
                    
            elif not re.search(r'^<.+>', line):
                #replace newlines, and make sure all quotes are with single quotes
                #becuase .csv files use double quotes to delimit a whole field
                text = '"' + line.replace('\n', '').replace('"', "'").strip() + '"'
            
        #end for line in file:
    #end for transcription in os.listdir(TRANSCRIPTION_PATH):
    
    
    
    MakeCSV(transcriptions_list)
    
    print("CSV file created successfully!")


    
    
#==============================================================================    
#---------------------------------Functions------------------------------------
#==============================================================================
##-------------------------------------------------------------------------
## GetTimestamp()
##-------------------------------------------------------------------------
##    Description:    Get the time, in seconds, of the current transcription segment
##
##    Arguments:      time; a string in the format MM:SS, minutes:seconds
##
##    Called By:      main()
##
##    Returns:        seconds; timestamp in seconds
##-------------------------------------------------------------------------
def GetTimestamp(time):
    seconds = 0
    
    min,sec = time.split(':')
    
    seconds = 60 * int(min) + int(sec)
    
    return str(seconds)

##-------------------------------------------------------------------------
## MakeCSV()
##-------------------------------------------------------------------------
##    Description:    Create a CSV file with the data
##
##    Arguments:      chunks; list of video chunk objects 
##
##    Called By:      main()
##-------------------------------------------------------------------------
def MakeCSV(transcriptions_list):
    
    with codec_open(OUTFILE, 'w', 'utf-8-sig') as outfile:
        outfile.write(','.join(LABELS.split()) + os.linesep)
        while len(transcriptions_list) > 0:
            HIT = random.sample(transcriptions_list, min(5, len(transcriptions_list)) )
            
            hit = [x.comma_delimited for x in HIT]
            outfile.write(",".join(hit) + os.linesep)
            
            
            transcriptions_list = set(transcriptions_list).difference(set(HIT))
        

#==============================================================================    
#----------------------------------Classes-------------------------------------
#==============================================================================
##-------------------------------------------------------------------------
## Class Classname
##-------------------------------------------------------------------------
##    Description:    A container class to split up a transcription into 
##                    timestamp chunks
##
##    Arguments:      transcription; a list of strings from a file.readlines() call
##
##    Properties:    self.info; list of all relevant info for each chunk
##                   self.comma_delimited; string representation of self.info
##
##-------------------------------------------------------------------------
class Chunk:
    def __init__(self, id, start, end, text, yt_id):
        self.info = [id, start, end, text, yt_id]
        self.comma_delimited = ",".join(self.info)
    
    def __repr__(self):
        return self.comma_delimited

        

#==============================================================================    
#------------------------------------------------------------------------------
#==============================================================================
if __name__ == "__main__":
    sys.exit( main() )