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
import pickle
import math
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

GOLD_HITS = { x.split()[0]:int(x.split()[1]) for x in open('Data/gold_file', 'r').readlines()}
VID_POLARITY = { x.split()[0]:x.split()[1] for x in open('Data/video_polarity.txt', 'r').readlines()}
cur = __import__(__name__)

TEXT_TIME_THRESHOLD = 20
AVERAGE_SCORE_THRESHOLD = 3
#==============================================================================
#-----------------------------------Main---------------------------------------
#==============================================================================
def main():
    #fragment_dict = defaultdict(list)
    #key = chunk_id of first chunk in hit 
    #value = Row object
    
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
                new_experiment.workers = set([x.worker_id for x in new_experiment.HIT_list])
            experiment_list.append( new_experiment )    
    #end for filename in os.listdir(MTURK_DIR):  
    
    
    #filter out spam from the experiment
    for e in experiment_list:
        if "Full" in e.name:
            e.FilterSpam(video_dict)
        else:
            e.FilterSpam(fragment_dict)
        
        ####OPTIONAL####
        #weights worker scores against the average scores for that task
        for hit in e.HIT_list:
            if 'Video' not in e.name:
                e.CompareAverages(hit)
    
    #print out the spam submissions
    with open('Data/spam_list.txt', 'w') as outfile:
        for e in experiment_list:    
            e.PrintSpamList(outfile)
            
    #print out a CSV to upload to MTurk, for automated rejections
    for e in experiment_list:
        e.AggregateData()
        e.UpdateMturkCSV(e.name)
    
    
    pass
#==============================================================================    
#---------------------------------Functions------------------------------------
#==============================================================================

##-------------------------------------------------------------------------
## Initialize()
##-------------------------------------------------------------------------
##    Description:     Import information from input CSVs and put them into
##                     into dictionaries
##
##    Returns:         fragment_dict; dictionary of Row objects
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
    
    
    with codec_open(full_CSV, 'rb') as full_csv:
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
            
            #this checks for the two cases where a text transcription 
            #fragments 5.1 and 14.1
            #was mistakenly omitted from the experiment. This ensures that
            #HITs with these fragments are not rejected for being incomplete
            if chunk_ids[0] == ('5.1'):
                chunk_ids = chunk_ids[1:]
                answer_polarities = answer_polarities[1:]
            elif chunk_ids[2] == ('14.1'):
                chunk_ids.pop(2)
                answer_polarities.pop(2)
                
            age,location = row[52].split('|')
            gender = row[53]

            temp = HIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities, age, location, gender)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
            
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
            vid_id = [row[27]]
            answer_polarity = [row[32]]
            age,location = row[30].split('|')
            gender = row[31]

            temp = HIT(hit_id, worker_id, work_time, vid_id, answer_polarity, age, location, gender)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
            
            HIT_list.append( temp )
    
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
    
    with codec_open(mturk_csv, 'rb') as audio_fragment_csv:
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
            
            temp = HIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities, age, location, gender)
            temp.transcriptions = set(chunk_transcriptions)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
            
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
    
    with codec_open(mturk_csv, 'rb') as audio_full_csv:
        f = list( csv.reader(audio_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = row[23]
            vid_id = [row[27]]
            vid_transcription = [row[33]]
            answer_polarity = [row[34]]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            temp = HIT(hit_id, worker_id, work_time, vid_id, answer_polarity, age, location, gender)
            temp.transcriptions = set(vid_transcription)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
            
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
    
    with codec_open(mturk_csv, 'rb') as text_fragment_csv:
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
            
            temp = HIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities, age, location, gender)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
                    
            HIT_list.append( temp )
    
    return HIT_list

def VideoFull(mturk_csv, experiment):
    #[0] = HITId
    #[15] = WorkerId
    #[23] = WorkTimeInSeconds
    #[27] = Input.id
    #[33] = Answer.â€œpolarityâ€
    HIT_list = []
    
    with codec_open(mturk_csv, 'rb') as text_full_csv:
        f = list( csv.reader(text_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = row[23]
            vid_id = [row[27]]
            answer_polarity = [row[33]]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            temp = HIT(hit_id, worker_id, work_time, vid_id, answer_polarity, age, location, gender)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
                    
            HIT_list.append( temp )
    
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
    
    with codec_open(mturk_csv, 'rb') as audio_fragment_csv:
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
            
            temp = HIT(hit_id, worker_id, work_time, chunk_ids, answer_polarities, age, location, gender)
            temp.transcriptions = set(chunk_transcriptions)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
                    
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
    
    with codec_open(mturk_csv, 'rb') as audio_full_csv:
        f = list( csv.reader(audio_full_csv) )
        for row in f[1:]:
            hit_id = row[0]
            worker_id = row[15]
            work_time = row[23]
            vid_id = [row[27]]
            vid_transcription = [row[33]]
            answer_polarity = [row[34]]
            age = row[30]
            location = row[31]
            gender = row[32]
            
            temp = HIT(hit_id, worker_id, work_time, vid_id, answer_polarity, age, location, gender)
            temp.transcriptions = set(vid_transcription)
            
            for field in [age,location,gender]:
                if 'select one' in field:
                    temp.reject_flag = True
                    temp.reject_reason = 'Pre-survey was left incomplete'
                    
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
##                    time; the length of the video (XmYs)
##
##    Properties:     self.id; the video ID number
##                    self.total_clip_length; the duration of the video in seconds
##-------------------------------------------------------------------------
class Video:
    def __init__(self, id, time):
        self.id = id
        self.total_clip_length = self.GetTimestamp(time)
        self.gold_value = None

    def GetTimestamp(self, time):
        minute,sec,__ = re_split('[ms]', time)
        seconds = 60 * int(minute) + int(sec)
        
        return seconds

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
## Class HIT
##-------------------------------------------------------------------------
##    Description:    Container class for a video fragment
##
##    Arguments:      hit_id; hit_id
##                    worker_id; worker_id
##                    work_time; time in seconds for completion of HIT
##                    id; list[], the id of the video/fragments
##                    polarity; list[], the sentiment scores of the video/fragments  
##
##    Properties:     self.hit_id; hit_id
##                    self.worker_id; worker_id
##                    self.work_time; time in seconds for completion of HIT
##                    self.ids = list[], the id of the video/fragments
##                    self.task_id = the id of the HIT, set to the id of the 
##                        video, or the first fragment id
##                    self.polarities; list[], the sentiment scores of the video/fragments
##                    self.reject_flag; flag for if a HIT is to be rejected 
##                        (i.e. it has been marked for spam)
##                    self.reject_reason; reason for having been marked as spam
##-------------------------------------------------------------------------
class HIT():
    def __init__(self, hit_id, worker_id, work_time, id, polarity, age, location, gender):
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.work_time = int( work_time )
        self.ids = id
        self.task_id = self.ids[0]
        self.age = age
        self.location = location
        self.gender = gender
        
        #the following try-block checks to make sure that none of the 
        #answers are 'select one', which means that a worker left a 
        #field blank
        try:
            self.polarities = [ int(p) for p in polarity ]
        except ValueError:
            self.reject_flag = True
            self.reject_reason = 'One or more answers were left blank'
        else:
            self.transcriptions = set()
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
##    Arguments:      name; the name of the experiment (TextFull, AVFragment, etc.)
##
##    Properties:     self.name; name of the experiment
##                    self.gender; Counter(), demographics for gender
##                    self.age; Counter(); demographics for age
##                    self.locaiton; Counter() demographics for location
##                    self.has_transcriptions; flag for if the experiment 
##                        is one that involves transcriptions
##-------------------------------------------------------------------------
class Experiment():
    def __init__(self, name):
        self.name = name
        self.kappa = "N/A"
        self.sigma = "N/A"
        self.kappa_spam = "N/A"
        self.sigma_spam = "N/A"
        self.frag_sigma = "N/A"
        self.average = "N/A"
        self.p_average = "N/A"
        self.m_average = "N/A"
        self.n_average = "N/A"
        self.workers = set()
        self.gender = Counter()
        self.age = Counter()
        self.location = Counter()
        
        self.has_transcriptions = False
        if name in HITS_WITH_TRANSCRIPTIONS:
            self.has_transcriptions = True
    
    
    ##-------------------------------------------------------------------------
    ## Experiment.FilterSpam()
    ##-------------------------------------------------------------------------
    ##    Description:     Filter out the spam from a list of HITs, using a 
    ##                     four-pass sweep.
    ##
    ##    Arguments:       answer_key; dict(), key=id value=Video/Row object
    ##
    ##
    ##    Calls:           Experiment.CheckTime()
    ##                     Experiment.CheckTranscriptions()
    ##                     Experiment.CheckGoldHIT()
    ##                     Experiment.AggregateData()
    ##-------------------------------------------------------------------------
    def FilterSpam(self, answer_key):
        self.answer_key = answer_key

        for hit in self.HIT_list:
            self.CheckTime(hit)
            
            #the following spam measures do not apply 
            #to the VideoFragment and VideoFull experiments
            if 'Video' not in self.name:
                if self.has_transcriptions:
                    self.CheckTranscriptions(hit)
                self.CheckGoldHIT(hit)
            
            
        #Aggregate all the scores now that spam has been removed
        #then call function to check averages
        self.AggregateData()
                
    ##-------------------------------------------------------------------------
    ## Experiment.CheckTime()
    ##-------------------------------------------------------------------------
    ##    Description:     Checks to make sure that a HIT was completed in a  
    ##                     time greater than the length of the video 
    ##                     or the cumulative length of the Fragments.
    ##
    ##    Arguments:       hit; a HIT object
    ##
    ##
    ##    Called by:       Experiment.FilterSpam()
    ##-------------------------------------------------------------------------
    def CheckTime(self, hit):
        if 'Text' in self.name:
            if hit.work_time <= TEXT_TIME_THRESHOLD:
                hit.reject_flag = True
                hit.reject_reason = 'Task was completed suspiciously quickly.'
        else:
            min_possible_completion_time = self.answer_key[hit.task_id].total_clip_length
            if hit.work_time <= min_possible_completion_time:
                hit.reject_flag = True
                hit.reject_reason = 'Task was submitted in a time shorter than the length of the video(s)'
    
    ##-------------------------------------------------------------------------
    ## Experiment.CheckTranscriptions()
    ##-------------------------------------------------------------------------
    ##    Description:     Checks to make sure that the partial transcriptions   
    ##                     in a HIT are acceptable according to these checks:
    ##                     (1) As many transcriptions are given as there were
    ##                         videos in the HIT, and that they are all unique
    ##                         as no HITs involve repeats.
    ##                     (2) The transcriptions provided are greater than 
    ##                         some set threshold, so that they are at least 
    ##                         of an acceptable length and not empty.
    ##
    ##    Arguments:       hit; a HIT object
    ##
    ##
    ##    Called by:       Experiment.FilterSpam()
    ##-------------------------------------------------------------------------
    def CheckTranscriptions(self, hit):
        if hit.reject_flag:
            return
        #if the set of transcriptions is less than 5, it means either:
        #1: transcriptions were not left for all five videos
        #2: there were fewer than 5 unique transcriptions
        if len(hit.transcriptions) < len(hit.ids):
            hit.reject_flag = True
            hit.reject_reason = 'Unique transcriptions were not provided for all five fragments'
            return
        
        #checks to make sure that each partial transcription given
        #is a string greater then N characters.
        #N = 20
        for t in hit.transcriptions:
            if len(t) <= 20:
                hit.reject_flag = True
                hit.reject_reason = 'One or more transcriptions were empty or were suspiciously short'
                return
    
    ##-------------------------------------------------------------------------
    ## Experiment.CheckGoldHIT()
    ##-------------------------------------------------------------------------
    ##    Description:     Checks to make sure that the answers given for    
    ##                     certain HITs are in agreement with golden answers.
    ##                     If the worker's answer is of an opposite polarity than 
    ##                     the golden answer, the HIT is flagged as spam.
    ##
    ##    Arguments:       hit; a HIT object
    ##
    ##
    ##    Called by:       Experiment.FilterSpam()
    ##-------------------------------------------------------------------------
    def CheckGoldHIT(self, hit):
        if hit.reject_flag:
            return
        for i in range( len(hit.ids) ):
            if hit.ids[i] in GOLD_HITS:
                gold_answer = GOLD_HITS[hit.ids[i]]
                worker_answer = hit.polarities[i]
                
                if gold_answer > 3:
                    if worker_answer <= 3:
                        hit.reject_flag = True
                        hit.reject_reason = 'One or more answers did not agree with Golden HIT answer'
                elif gold_answer < 3:
                    if worker_answer >= 3:
                        hit.reject_flag = True
                        hit.reject_reason = 'One or more answers did not agree with Golden HIT answer'
    
    ##-------------------------------------------------------------------------
    ## Experiment.CompareAverages()
    ##-------------------------------------------------------------------------
    ##    Description:     Compares a worker's scores with the average of all
    ##                     workers' answers. If the current worker's answer is
    ##                     off by a certain amount (set by AVERAGE_SCORE_THRESHOLD)
    ##                     the HIT is flagged as spam.    
    ##
    ##    Arguments:       hit; a HIT object
    ##
    ##
    ##    Called by:       Experiment.FilterSpam()
    ##-------------------------------------------------------------------------
    def CompareAverages(self, hit):
        if hit.reject_flag:
            return
        for i in range( len(hit.ids) ):
            cur_id = hit.ids[i]
            cur_score = hit.polarities[i]
            
            difference = abs( self.sentiment_averages[cur_id] - cur_score )
            
            if difference > AVERAGE_SCORE_THRESHOLD:
                hit.reject_flag = True
                hit.reject_reason = 'One or more answers did not agree with a Golden HIT answer(X)'
                return
            

    ##-------------------------------------------------------------------------
    ## Experiment.AggregateData()
    ##-------------------------------------------------------------------------
    ##    Description:     Compiles all of the data from the experiment 
    ##                     for filtered, non-spam submissions
    ##                     
    ##                     dict( key=id value=Counter(key=score value=count) )
    ##                     And then builds a dictionary of the average score
    ##                     for a given id.  
    ##
    ##                     Counter() for each demographic field:
    ##                         age
    ##                         location
    ##                         gender
    ##-------------------------------------------------------------------------
    def AggregateData(self):
        self.sentiment_scores = defaultdict(lambda: Counter())
        s_scores_spam = defaultdict(lambda: Counter())
        combined_s_scores = defaultdict(lambda: Counter()) # averages scores of each fragment for interfragment agreement
        total_counts = Counter()
        self.sentiment_averages = defaultdict(float)
        
        
        temp = [x for x in self.HIT_list if not x.reject_flag]
        for hit in temp:
            #worker demographics
            self.age[hit.age] += 1
            self.gender[hit.gender] += 1
            self.location[hit.location] += 1
            
            for i in range( len(hit.ids) ):
                self.sentiment_scores[hit.ids[i]][hit.polarities[i]] += 1
                s_scores_spam[hit.ids[i]][hit.polarities[i]] += 1
                total_counts[hit.ids[i]] += 1

        if "Fragment" in self.name:
            average_per_frag = dict()

            for fragment in self.sentiment_scores:
                average = 0
                n = 0
                for j in self.sentiment_scores[fragment]:
                    average += j*self.sentiment_scores[fragment][j]
                    n += self.sentiment_scores[fragment][j]
                average_per_frag[fragment] = float(average)/n

            for fragment in average_per_frag:
                vid = fragment.split('.')[0]
                combined_s_scores[vid][average_per_frag[fragment]] += 1
            self.frag_sigma = self.std_dev(combined_s_scores)
        
        temp = [x for x in self.HIT_list if x.reject_flag]
        for hit in temp:    
            for i in range( len(hit.ids) ):
                try:
                    s_scores_spam[hit.ids[i]][hit.polarities[i]] += 1
                except AttributeError:
                    continue

        
        for id in self.sentiment_scores:
            score_Counter = self.sentiment_scores[id]
            total = 0
            count = 0
            for score in score_Counter:
                total += score * score_Counter[score] 
                count += score_Counter[score]
            
            self.sentiment_averages[id] = float(total) / count

        total = 0
        count = 0
        p_total = 0
        p_count = 0
        m_total = 0
        m_count = 0
        n_total = 0
        n_count = 0

        for id in self.sentiment_averages:
            vidid = id.split('.')[0]
            total += self.sentiment_averages[id]
            count += 1
            if VID_POLARITY[vidid] == 'p':
                p_total += self.sentiment_averages[id]
                p_count += 1
            if VID_POLARITY[vidid] == 'm':
                m_total += self.sentiment_averages[id]
                m_count += 1
            if VID_POLARITY[vidid] == 'n':
                n_total += self.sentiment_averages[id]
                n_count += 1

        self.average = float(total)/count
        self.p_average = float(p_total)/p_count
        self.m_average = float(m_total)/m_count
        self.n_average = float(n_total)/n_count

        self.kappa = self.fleiss_kappa_iaa(self.sentiment_scores)
        self.sigma = self.std_dev(self.sentiment_scores)

        self.kappa_spam = self.fleiss_kappa_iaa(s_scores_spam)
        self.sigma_spam = self.std_dev(s_scores_spam)

    # calculates Fleiss Kappa interannotator agreement score
    def fleiss_kappa_iaa(self, s_scores):
        k = 5 # number of sentiment categories
        N = len(s_scores) # number of fragments/videos
        n = 0 # number of ratings per subject
        for fragment in s_scores:
            for j in range(1,6):
                n += s_scores[fragment][j]
        n = float(n)/N
        
        # proportion of all assigments to the jth category (score)
        P_j = Counter() # P_j[score] = proportion
        for j in range(1,6):
            for fragment in s_scores:
                P_j[j] += float(s_scores[fragment][j])
        for j in range(1,6):
            P_j[j] = (P_j[j]/(N*10))**2

        P_i = Counter()
        for fragment in s_scores:
            for j in range(1, 6):
                P_i[fragment] += float(s_scores[fragment][j]**2)


            P_i[fragment] = (P_i[fragment] - n)/(n*(n-1))


        # mean agreement
        P_mean = sum(P_i.values())/N
        # mean expected value
        P_e_mean = sum(P_j.values()) 

        return (P_mean - P_e_mean)/ (1 - P_e_mean)
    
    # calculate the standard deviation for the given sentiment scores
    def std_dev(self, s_scores):
        summed_sigmas = 0.0
        for fragment in s_scores:
            summed_score = 0
            n = 0
            for j in s_scores[fragment]:
                summed_score += j*s_scores[fragment][j]
                n += s_scores[fragment][j]
            average = float(summed_score)/n
            summed_squares = 0
            for j in s_scores[fragment]:
                summed_squares += ((j-average)**2)*s_scores[fragment][j]
            summed_sigmas += math.sqrt(summed_squares/n)
        return summed_sigmas/len(s_scores)

    ##-------------------------------------------------------------------------
    ## Experiment.PrintSpamList()
    ##-------------------------------------------------------------------------
    ##    Description:     Prints out all of the HITs that were flagged as spam  
    ##
    ##    Arguments:       outfile_stream; an opened file. 
    ##                         if not None, prints to stdout, else prints to file
    ##-------------------------------------------------------------------------
    def PrintSpamList(self, outfile_stream = None):
        if outfile_stream:
            sys.stdout = outfile_stream
        
        spam_list = [hit for hit in self.HIT_list if hit.reject_flag]
        print('#'*50)
        print(self.name + ': %s spam HITs out of %s total HITs' % (str(len(spam_list)), str(len(self.HIT_list))))
        print('Fleiss Kappa: ' + str(self.kappa) )
        print('Fleiss Kappa+spam: ' + str(self.kappa_spam) )
        print('Average deviation: ' + str(self.sigma))
        print('Average deviation+spam: ' + str(self.sigma_spam))
        print('Interfragment deviation: ' + str(self.frag_sigma))
        print('Average: ' + str(self.average))
        print('Positive average: ' + str(self.p_average))
        print('Mixed average: ' + str(self.m_average))
        print('Negative average: ' + str(self.n_average))
        print('#'*50)
        for hit in spam_list:
            print("\t".join([hit.hit_id, hit.worker_id, hit.reject_reason]))
        print()
    
    ##-------------------------------------------------------------------------
    ## Experiment.UpdateMturkCSV()
    ##-------------------------------------------------------------------------
    ##    Description:     Prints out all of the HITs that were flagged as spam  
    ##
    ##    Arguments:       outfile_stream; an opened file. 
    ##                         if not None, prints to stdout, else prints to file
    ##-------------------------------------------------------------------------
    def UpdateMturkCSV(self, name):
        csv_original = list( csv.reader(codec_open(os.path.join(MTURK_DIR,name + "_results.csv"), 'rb')) ) 
        
        filtered_dir = os.getcwd() + '/filtered'
        with codec_open(os.path.join(filtered_dir, name + "_results_filtered.csv"), 'w') as csv_filtered:
            csv_writer = csv.writer(csv_filtered)
            for i in range( len(csv_original) ):
                if i == 0:
#                     AssignmentStatus = csv_original[0].index('AssignmentStatus')
#                     RequesterFeedback = csv_original[0].index('RequesterFeedback')
#                     Reject = csv_original[0].index('Reject')
                    pass
                
                else: 
                    hit = self.HIT_list[i-1]
                    if hit.reject_flag:
                        #csv_original[i][AssignmentStatus] = 'Rejected'
                        #csv_original[i][RequesterFeedback] = hit.reject_reason
                        csv_original[i].append('') 
                        csv_original[i].append( hit.reject_reason )
                csv_writer.writerow(csv_original[i])
#                 csv_filtered.write(",".join(csv_original[i]))     
#                 csv_filtered.write(os.linesep)  

        

#==============================================================================    
#------------------------------------------------------------------------------
#==============================================================================
if __name__ == "__main__":
    sys.exit( main() )