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
from collections import defaultdict,Counter
from re import split as re_split
#==============================================================================
#--------------------------------Constants-------------------------------------
#==============================================================================
DEBUG = True
fragment_HIT = 'Data/575_HIT.csv'
full_CSV = 'Data/575_youtube_video_collection.csv'
MTURK_DIR = os.getcwd() + '/MTurk_results'

HITS_WITH_TRANSCRIPTIONS = ['AudioFragment', 'AudioFull', 'AVFragment', 'AVFull']

GOLD_HITS = { x.split()[0]:int(x.split()[1]) for x in open('DATA/gold_file', 'r').readlines()}
cur = __import__(__name__)

TEXT_TIME_THRESHOLD = 20
#==============================================================================
#-----------------------------------Main---------------------------------------
#==============================================================================
def main():
    #fragment_dict = defaultdict(list)
    #key = chunk_id of first chunk in hit 
    #value = tuple(cumulative length of all chunks in seconds, list of Fragment objects
    
    #video_dict = defaultdict(Video)
    #key = video_id 
    #value = Video object
    
    fragment_dict, video_dict = Initialize()
    experiment_list = []
    
    for filename in os.listdir(MTURK_DIR):
        if not filename[0] == '.':
            name = filename.split('_')[0]
            filename = os.path.join(MTURK_DIR, filename)
            new_experiment = Experiment(name)
            
            try:
                CSV_func = getattr(cur, name)
            except AttributeError:
                print( 'function not found "%s" (%s)' % (name, filename) )
                sys.exit(1)
            else:
                new_experiment.HIT_list = CSV_func(filename, new_experiment)
            
            experiment_list.append( new_experiment )
    
            print( filename )
    #end for filename in os.listdir(MTURK_DIR):  
    for e in experiment_list:
        if "Full" in e.name:
            e.FilterSpam(video_dict)
        else:
            e.FilterSpam(fragment_dict)
    
    
    print("Hello, World!")
#==============================================================================    
#---------------------------------Functions------------------------------------
#==============================================================================

##-------------------------------------------------------------------------
## Initialize()
##-------------------------------------------------------------------------
##    Description:     Import information from input CSVs and put them into
##                     into dictionaries
##
##        Returns:     fragment_dict; dictionary of Row objects
##-------------------------------------------------------------------------
def Initialize():
    #key = chunk_id of first chunk in hit 
    #value = Row object
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
            
            cur_row = Row(total_clip_time, fragment_list)
            fragment_dict[fragment_list[0].id] = cur_row
    
    
    with codec_open(full_CSV, 'rb', 'utf-8') as full_csv:
        f = list( csv.reader(full_csv) )
        for row in f[1:]:
            temp = Video(row[0], row[5])
            video_dict[temp.id] = temp
    
    return fragment_dict,video_dict
##-------------------------------------------------------------------------
## Functions for extracting completed HITs from MTurk CSVs
##-------------------------------------------------------------------------
##    Description:     Take an MTurk produced CSV of the results of the 
##                     HIT online, and import the tasks submitted into the
##                     program.
##
##    Arguments:       mturk_csv; MTurk produced CSV of HIT results
##
##
##    Returns:         HIT_list; list of all the submitted HITs
##-------------------------------------------------------------------------
def TextFragment(mturk_csv, experiment):
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
            work_time = row[23]
            chunk_ids = row[27:52:5]
            answer_polarities = row[54:59]
            age,location = row[52].split('|')
            gender = row[53]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            
            HIT_list.append( temp )
    
    return HIT_list

def TextFull(mturk_csv, experiment):
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
            work_time = row[23]
            vid_id = row[27]
            answer_polarity = row[32]
            age,location = row[30].split('|')
            gender = row[31]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            HIT_list.append( FullHIT(hit_id, worker_id, work_time, vid_id, answer_polarity) )
    
    return HIT_list
    
def AudioFragment(mturk_csv, experiment):
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
            work_time = row[23]
            chunk_ids = row[27:52:5]
            chunk_transcriptions = row[55:60]
            answer_polarities = row[60:65]
            age = row[52]
            location = row[53]
            gender = row[54]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            temp.chunk_transcriptions = set(chunk_transcriptions)
            
            HIT_list.append( temp )
    
    return HIT_list

def AudioFull(mturk_csv, experiment):
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
            work_time = row[23]
            vid_id = row[27]
            vid_transcription = row[33]
            answer_polarity = row[34]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, vid_id, answer_polarity)
            temp.vid_transcription = set([vid_transcription])
            
            HIT_list.append( temp )
    
    return HIT_list

def VideoFragment(mturk_csv, experiment):
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
    #age_index = label_bar.index('Answer.Age')
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb', 'utf-8') as text_fragment_csv:
        f = list( csv.reader(text_fragment_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = row[23]
            chunk_ids = row[27:52:5]
            answer_polarities = row[55:60]
            age = row[52]
            location = row[53]
            gender = row[54]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            
            HIT_list.append( temp )
    
    return HIT_list

def VideoFull(mturk_csv, experiment):
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
            work_time = row[23]
            vid_id = row[27]
            answer_polarity = row[33]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            HIT_list.append( FullHIT(hit_id, worker_id, work_time, vid_id, answer_polarity) )
    
    return HIT_list
    
def AVFragment(mturk_csv, experiment):
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
            work_time = row[23]
            chunk_ids = row[27:52:5]
            chunk_transcriptions = row[55:60]
            answer_polarities = row[60:65]
            age = row[52]
            location = row[53]
            gender = row[54]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities)
            temp.chunk_transcriptions = set(chunk_transcriptions)
            
            HIT_list.append( temp )
    
    return HIT_list

def AVFull(mturk_csv, experiment):
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
            work_time = row[23]
            vid_id = row[27]
            vid_transcription = row[33]
            answer_polarity = row[34]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            #worker demographics
            experiment.age[age]
            experiment.gender[gender]
            experiment.location[location]
            
            temp = FragmentHIT(hit_id, worker_id, work_time, vid_id, answer_polarity)
            temp.vid_transcription = set([vid_transcription])
            
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
        self.total_clip_length = self.GetTimestamp(time)
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
        self.task_id = self.chunk_ids[0]
        self.chunk_polarities = chunk_polarities
        
        self.chunk_transcriptions = set()
        self.reject_flag = False
        self.reject_reason = ''
        
        
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
        self.vid_id = vid_id
        self.task_id = self.vid_id
        self.vid_polarity = vid_polarity
        
        self.vid_transcription = set()
        self.reject_flag = False
        self.reject_reason = ''
        
##-------------------------------------------------------------------------
## Class Row
##-------------------------------------------------------------------------
##    Description:    Container class for a row of chunks, from the fragment CSV
##
##    Arguments:      total_clip_length; the total length of all clips in a 
##                        row of the fragment CSV
##                    fragment_list; list of Fragment objects
##-------------------------------------------------------------------------
class Row():
    def __init__(self, total_clip_length, fragment_list):
        self.total_clip_length = total_clip_length
        self.fragment_list = fragment_list


##-------------------------------------------------------------------------
## Class Experiment
##-------------------------------------------------------------------------
##    Description:    Container class for each experiment
##                    i.e. text only, audio only, etc. etc.
##
##    Arguments:      total_clip_length; the total length of all clips in a 
##                        row of the fragment CSV
##                    fragment_list; list of Fragment objects
##-------------------------------------------------------------------------
class Experiment():
    def __init__(self, name):
        self.name = name
        
        self.sentiment_scores = defaultdict(lambda: Counter())
        self.gender = Counter()
        self.age = Counter()
        self.location = Counter()
        
        self.has_transcriptions = False
        if name in HITS_WITH_TRANSCRIPTIONS:
            self.has_transcriptions = True
    
    
    def FilterSpam(self, answer_key):
        self.answer_key = answer_key
        for HIT in self.HIT_list:
            self.CheckTime(HIT)
            if self.has_transcriptions:
                self.CheckTranscriptions(HIT)
            self.CompareAverages(HIT)
            
        print('filtered')
    
    
    def CheckTime(self, HIT):
        if 'Text' in self.name:
            if HIT.work_time <= TEXT_TIME_THRESHOLD:
                HIT.reject_flag = True
                HIT.reject_reason = 'Task was completed suspiciously quickly.'
        else:
            min_possible_completion_time = self.answer_key[HIT.task_id].total_clip_length
            if HIT.work_time <= min_possible_completion_time:
                HIT.reject_flag = True
                HIT.reject_reason = 'Task was submitted in a time shorter than the length of the video(s)'
    
    
    def CheckTranscriptions(self, HIT):
        if len(HIT.chunk_transcriptions) < 5:
            HIT.reject_flag = True
            HIT.reject_reason = 'Unique transcriptions were not provided for all five fragments'
            return
        
        #checks to make sure that each partial transcription given
        #is a string greater then N characters.
        #N = 20
        for t in HIT.chunk_transcriptions:
            if len(t) <= 20:
                HIT.reject_flag = True
                HIT.reject_reason = 'One or more transcriptions were empty or were suspiciously short'
    
    
    def CompareAverages(self, HIT):
        print('Compared')
        


        

#==============================================================================    
#------------------------------------------------------------------------------
#==============================================================================
if __name__ == "__main__":
    sys.exit( main() )