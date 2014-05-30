# -*- coding: utf-8 -*-
'''
#==============================================================================
SpamFilter
@author: aelshen
#==============================================================================
'''

import os
import sys
import csv
from codecs import open as codec_open
from collections import defaultdict
from re import split as re_split
#==============================================================================
#--------------------------------Constants-------------------------------------
#==============================================================================
DEBUG = True

#==============================================================================
#-----------------------------------Main---------------------------------------
#==============================================================================
def main():
    fragment_HIT = '575_HIT.csv'
    full_CSV = '575_youtube_video_collection.csv'
    
    
    #key = chunk_id of first chunk in hit 
    #value = tuple(cumulative length of all chunks in seconds, list of Fragment objects
    fragment_dict = defaultdict(list) 
    
    #key = video_id 
    #value = Video object
    video_dict = defaultdict(Video)
    
    with codec_open(fragment_HIT, 'rb', 'utf-8') as fragment_csv:
        f = list( csv.reader(fragment_csv) )
        for row in f[1:]:
            fragment_list = []
            total_clip_time = 0
            
            chunks = [ row[i:i+5] for i in range(0, len(row), 5) ]
            for c in chunks:
                temp = Fragment(c[0], c[1], c[2], c[3])
                total_clip_time += temp.duration
                fragment_list.append( temp )
            
            fragment_dict[fragment_list[0].id] = (total_clip_time, fragment_list)
    
    with codec_open(full_CSV, 'rb', 'utf-8') as full_csv:
        f = list( csv.reader(full_csv) )
        for row in f[1:]:
            temp = Video(row[0], row[5])
            video_dict[temp.id] = temp
    
    print("Hello, World!")
#==============================================================================    
#---------------------------------Functions------------------------------------
#==============================================================================
##-------------------------------------------------------------------------
## test()
##-------------------------------------------------------------------------
##    Description:        description
##
##    Arguments:        arguments
##
##    Calls:                calls
##
##        Returns:            returns
##-------------------------------------------------------------------------
def TextFragment(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.chunk_1_id
    #[32] = Input.chunk_2_id
    #[37] = Input.chunk_3_id
    #[42] = Input.chunk_4_id
    #[47] = Input.chunk_5_id
    #[60] = Answer.â€œchunk_1_polarityâ€
    #[61] = Answer.â€œchunk_2_polarityâ€
    #[62] = Answer.â€œchunk_3_polarityâ€
    #[63] = Answer.â€œchunk_4_polarityâ€
    #[64] = Answer.â€œchunk_5_polarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as text_fragment_csv:
        f = list( csv.reader(text_fragment_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            chunk_ids = row[27:47:5]
            answer_polarities = row[60:64]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            
            HIT_list.append( temp )
    
    return HIT_list

def TextFull(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.id
    #[33] = Answer.â€œpolarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as text_full_csv:
        f = list( csv.reader(text_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            vid_id = row[27]
            answer_polarity = row[33]
            
            HIT_list.append( FullHIT(hit_id, worker_id, work_time, vid_id, answer_polarity) )
    
    return HIT_list
    
def AudioFragment(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.chunk_1_id
    #[32] = Input.chunk_2_id
    #[37] = Input.chunk_3_id
    #[42] = Input.chunk_4_id
    #[47] = Input.chunk_5_id
    #[55] = Answer.chunk_1_transcription
    #[56] = Answer.chunk_2_transcription
    #[57] = Answer.chunk_3_transcription
    #[58] = Answer.chunk_4_transcription
    #[59] = Answer.chunk_5_transcription
    #[60] = Answer.â€œchunk_1_polarityâ€
    #[61] = Answer.â€œchunk_2_polarityâ€
    #[62] = Answer.â€œchunk_3_polarityâ€
    #[63] = Answer.â€œchunk_4_polarityâ€
    #[64] = Answer.â€œchunk_5_polarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as audio_fragment_csv:
        f = list( csv.reader(audio_fragment_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            chunk_ids = row[27:47:5]
            chunk_transcriptions = row[55:59]
            answer_polarities = row[60:64]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            temp.chunk_transcriptions = chunk_transcriptions
            
            HIT_list.append( temp )
    
    return HIT_list

def AudioFull(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.id
    #[28] = Input.transcription
    #[33] = Answer.partial_transcription
    #[34] = Answer.â€œpolarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as audio_full_csv:
        f = list( csv.reader(audio_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            vid_id = row[27]
            vid_transcription = row[33]
            answer_polarity = row[34]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, vid_id, answer_polarity)
            temp.vid_transcription = vid_transcription
            
            HIT_list.append( temp )
    
    return HIT_list

def VideoFragment(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.chunk_1_id
    #[32] = Input.chunk_2_id
    #[37] = Input.chunk_3_id
    #[42] = Input.chunk_4_id
    #[47] = Input.chunk_5_id
    #[60] = Answer.â€œchunk_1_polarityâ€
    #[61] = Answer.â€œchunk_2_polarityâ€
    #[62] = Answer.â€œchunk_3_polarityâ€
    #[63] = Answer.â€œchunk_4_polarityâ€
    #[64] = Answer.â€œchunk_5_polarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as video_fragment_csv:
        f = list( csv.reader(video_fragment_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            chunk_ids = row[27:47:5]
            answer_polarities = row[60:64]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            
            HIT_list.append( temp )
    
    return HIT_list

def VideoFull(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.id
    #[33] = Answer.â€œpolarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as video_full_csv:
        f = list( csv.reader(video_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            vid_id = row[27]
            answer_polarity = row[33]
            
            HIT_list.append( FullHIT(hit_id, worker_id, work_time, vid_id, answer_polarity) )
    
    return HIT_list
    
def AVFragment(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.chunk_1_id
    #[32] = Input.chunk_2_id
    #[37] = Input.chunk_3_id
    #[42] = Input.chunk_4_id
    #[47] = Input.chunk_5_id
    #[55] = Answer.chunk_1_transcription
    #[56] = Answer.chunk_2_transcription
    #[57] = Answer.chunk_3_transcription
    #[58] = Answer.chunk_4_transcription
    #[59] = Answer.chunk_5_transcription
    #[60] = Answer.â€œchunk_1_polarityâ€
    #[61] = Answer.â€œchunk_2_polarityâ€
    #[62] = Answer.â€œchunk_3_polarityâ€
    #[63] = Answer.â€œchunk_4_polarityâ€
    #[64] = Answer.â€œchunk_5_polarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as av_fragment_csv:
        f = list( csv.reader(av_fragment_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            chunk_ids = row[27:47:5]
            chunk_transcriptions = row[55:59]
            answer_polarities = row[60:64]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            temp.chunk_transcriptions = chunk_transcriptions
            
            HIT_list.append( temp )
    
    return HIT_list

def AVFull(mturk_csv):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.id
    #[28] = Input.transcription
    #[33] = Answer.partial_transcription
    #[34] = Answer.â€œpolarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as av_full_csv:
        f = list( csv.reader(av_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = [23]
            vid_id = row[27]
            vid_transcription = row[33]
            answer_polarity = row[34]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, vid_id, answer_polarity)
            temp.vid_transcription = vid_transcription
            
            HIT_list.append( temp )
    
    return HIT_list





#==============================================================================    
#----------------------------------Classes-------------------------------------
#==============================================================================
##-------------------------------------------------------------------------
## Class Video
##-------------------------------------------------------------------------
##    Description:    Container class for a video 
##
##    Arguments:      id; the video ID number
##                    start_time; the start time of the video in seconds
##                    end_time; the end time of the video in seconds
##
##    Properties:     self.id; the video ID number
##                    self.duration; the duration of the fragment in seconds
##-------------------------------------------------------------------------
class Video:
    def __init__(self, id, time):
        self.id = id
        self.duration = self.GetTimestamp(time)
        self.gold_value = None

    def GetTimestamp(self, time):
        minute,sec,__ = re_split('[ms]', time)
        seconds = 60 * int(minute) + int(sec)
        
        return str(seconds)

##-------------------------------------------------------------------------
## Class Fragment
##-------------------------------------------------------------------------
##    Description:    Container class for a video fragment
##
##    Arguments:      id; the fragment ID number
##                    start_time; the start time of the fragment in seconds
##                    end_time; the end time of the fragment in seconds
##
##    Properties:     self.id; the fragment ID number
##                    self.duration; the duration of the fragment in seconds
##-------------------------------------------------------------------------
class Fragment:
    def __init__(self, id, start_time, end_time, transcription):
        self.id = id
        self.transcription = transcription
        self.duration = int(end_time) - int(start_time)
        self.gold_value = None


##-------------------------------------------------------------------------
## Class FragmentHIT
##-------------------------------------------------------------------------
##    Description:    Container class for a video fragment
##
##    Arguments:      id; the fragment ID number
##                    start_time; the start time of the fragment in seconds
##                    end_time; the end time of the fragment in seconds
##
##    Properties:     self.id; the fragment ID number
##                    self.duration; the duration of the fragment in seconds
##-------------------------------------------------------------------------
class FragmentHIT():
    def __init__(self, hit_id, worker_id, work_time, chunk_ids, chunk_polarities):
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.work_time = int( work_time )
        self.chunk_ids = chunk_ids
        self.chunk_polarities = chunk_polarities
        
        self.chunk_transcriptions = []
        
        
##-------------------------------------------------------------------------
## Class FullHIT
##-------------------------------------------------------------------------
##    Description:    Container class for a video fragment
##
##    Arguments:      id; the fragment ID number
##                    start_time; the start time of the fragment in seconds
##                    end_time; the end time of the fragment in seconds
##
##    Properties:     self.id; the fragment ID number
##                    self.duration; the duration of the fragment in seconds
##-------------------------------------------------------------------------
class FullHIT():
    def __init__(self, hit_id, worker_id, work_time, vid_id, vid_polarity):
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.work_time = int( work_time ) 
        self.vid_id
        self.vid_polarity
        
        self.vid_transcription = []
        
        

#==============================================================================    
#------------------------------------------------------------------------------
#==============================================================================
if __name__ == "__main__":
    sys.exit( main() )