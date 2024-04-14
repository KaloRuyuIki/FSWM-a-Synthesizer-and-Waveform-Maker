#modules
import scipy.io.wavfile as wav
from scipy import fft
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
import tkinter.filedialog as fd
import parselmouth as prt
import os
import types
from pydub import AudioSegment
#from librosa.effects import pitch_shift as ps
import regex as re
import pyaudio as pad
import wave
import random as rd
import struct as st
import pygame as pyg
import time
import ctypes
import types
from xml import sax
##import re
##import midiutil.MidiFile as mdf

#constants
__product__ = "FSWM: Synthesizer & WAV-file Maker"
__version__ = "0.4.1"
PI=np.pi
TAU=2*np.pi
INT=np.int32
SRT=np.int8
AMPL=np.iinfo(INT).max
INF=float('inf')

#pretreatment
plt.ion()
ctypes.windll.shcore.SetProcessDpiAwareness(1)

#define

def filesuf(file,suf):
    return file if file.endswith(suf) else file+suf
def towav(file,res):
    f=AudioSegment.from_file(file)
    f.export(res if res[-4:]=='.wav' else res+'.wav','wav')    
def record(filen,time,device=None,track=1,rate=44100):
    filen=filen if filen[-4:]=='.wav' else filen+'.wav'
    pa=pad.PyAudio()
    devi=None
    if device=='PC':
        for i in range(pa.get_device_count()):
            d=pa.get_device_info_by_index(i)
            if '立体声混音' in d['name']:
                devi=i
                break
    chunk = 1024 
    sample_format = pad.paInt32
    stream = pa.open(format=sample_format, channels=track,
                     rate=rate, input=True,
                     input_device_index=devi,
                     frames_per_buffer=chunk)
    print("Record")
    frames = []
    for i in range(0, int(rate / chunk * time)):
        data = stream.read(chunk)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    pa.terminate()
    print('Done')
    with wave.open(filen, 'wb') as sf:
        sf.setnchannels(track)
        sf.setsampwidth(pa.get_sample_size(sample_format))
        sf.setframerate(rate)
        sf.writeframes(b''.join(frames))
        
class FehError(Exception):
    '''The Exception of FehWAVMaker'''
    
class FreqCalcNum:
    def __init__(self,eqtp=12,do=0,do_oct=-1,A=440):
        """
        if eqpt==12:
            do=0  A 440
            do=3  C 
        """
        self.A=A
        self.e=eqtp
        if not 0<=do<eqtp:raise FehError("%d超过了%d平均律的范围" % (do,eqtp))
        self.do=A*2**(do/eqtp+do_oct)
    __repr__=__str__=lambda self:'(A=%.2f,do=%.2f,eq=%d)'%(self.A,self.do,self.e)
    def num2freq(self,i,o=0):
        if not 0<=i<self.e:raise FehError("%d超过了%d平均律的范围" % (i,self.e))
        return round(self.do*2**(o+i/self.e),10)
class FreqCalcANSI(FreqCalcNum):
    def __init__(self,notes,A=440):
        self.notes,self.C=notes,notes.index('C')
        super().__init__(len(notes),self.C,-1,A)
    def ansi2freq(self,note,m=0):
        if note=='O':return 0
        return self.num2freq((self.notes.index(note)-self.C)%len(self.notes),m)
spfc={12:FreqCalcANSI(['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']),
      19:FreqCalcANSI(['A','A#','Bb','B','B#','C','C#','Db','D','D#',
                     'Eb','E','E#','F','F#','Gb','G','G#','Ab']),
      24:FreqCalcANSI(['A','A_','A#','Bd','B','B_','C','C_','C#','Dd','D','D_',
                       'D#','Ed','E','E_','F','F_','F#','Gd','G','G_','G#','Ad'])
      }
fc=spfc[12]

class PreviewWav:
    def __init__(self,filen):
        self.fn=filen if filen[-4:]=='.wav' else filen+'.wav'
    def play(self):
        os.system("start "+self.fn)
    def __sw_abs(self,audio,r,plt1,plt2,plt3):
        fftres = fft.fft(audio)
        fftlen = len(fftres)//2
        rg = fft.fftfreq(len(fftres),1/r)[:fftlen]
        plt.subplot(plt1)
        plt.plot(np.linspace(0,len(audio)/r,len(audio)),audio)
        plt.subplot(plt2)
        f=np.abs(fftres)/(len(audio)/2)
        plt.plot(rg,f[:fftlen])
        plt.subplot(plt3)
        f2=np.angle(fftres)
        plt.plot(rg,f2[:fftlen])
        return f,f2
    def show_wave(self,range=(None,None),to1tr=False):
        plt.figure(figsize=(12,6))
        r,audio=wav.read(self.fn)
        maxx=np.iinfo(audio.dtype).max
        audio=audio/maxx
        range=(0 if range[0] is None else int(range[0]*r),
               (len(audio) if len(audio.shape)==1 else np.size(audio,0))
               if range[1] is None else int(range[1]*r))
        th=[None,None,None,None]
        if len(audio.shape)==2 and to1tr:
            audio=np.sum(audio.T,0)/2
        if len(audio.shape)==2:
            audio=audio.T
            a1,a2=audio[0][range[0]:range[1]],audio[1][range[0]:range[1]]
            th[0:2]=self.__sw_abs(a1,r,321,323,325)
            th[2:4]=self.__sw_abs(a2,r,322,324,326)
        else:
            audio=audio[range[0]:range[1]]
            th[0:2]=self.__sw_abs(audio,r,211,223,224)
        plt.show()
        return th
    def __notes12(self):
        pass
    def show_sgpt(self,enhance=True,maxf=4000,freq=True,intn=True):
        al=1+freq+intn
        plt.figure(figsize=(10,6))
        plt.subplot(al*100+11)
        snd = prt.Sound(self.fn)
        pre_emphasized_snd = snd.copy()
        pre_emphasized_snd.pre_emphasize()
        spectrogram = pre_emphasized_snd.to_spectrogram(window_length=0.03,
                                                        maximum_frequency=maxf)
        X, Y = spectrogram.x_grid(), spectrogram.y_grid()
        if enhance:
            sg_db = 10 * np.log10(spectrogram.values)
            vmin=sg_db.max()-70
            sg_db[np.where(sg_db==-np.inf)]=vmin
        else:
            sg_db = spectrogram.values
            vmin=sg_db.min()
        plt.pcolormesh(X, Y, sg_db, vmin=vmin, cmap='afmhot')
        plt.xlim([snd.xmin, snd.xmax])
        plt.ylim([spectrogram.ymin, spectrogram.ymax])
        plt.xlabel("time [s]")
        plt.ylabel("spectrogram frequency [Hz]")

        if freq:
            plt.subplot(al*100+12)
            pitch = snd.to_pitch()
            #print(pitch)
            pitch_values = pitch.selected_array['frequency']
            maxf = int(pitch_values.max())
            maxf = round(maxf+10**(len(str(maxf))-1),-len(str(maxf))+1)
            pitch_values[pitch_values==0] = np.inf
            try:
                minf = int(pitch_values.min())
                minf = round(10**(len(str(minf))-1),-len(str(minf))+1)
            except:
                minf = 0
            if maxf>0:
                pitch_values[pitch_values==np.inf] = np.nan
                plt.plot(pitch.xs(), pitch_values, 'o', markersize=6, color='w')
                plt.plot(pitch.xs(), pitch_values, 'o', markersize=3, color='#B5C9C9')
                plt.grid(False)
                plt.ylim(minf, maxf)
            plt.ylabel("fundamental frequency [Hz]")
            
            k=-3
            while True:
                f=fc.ansi2freq('C',k)
                if f>maxf:
                    break
                plt.axline((0,f),(1,f),lw=1,color='red')
                for i in 'DEFGAB':
                    f=fc.ansi2freq(i,k)
                    plt.axline((0,f),(1,f),lw=1,color='#81C9C9')
                for i in 'CDFGA':
                    f=fc.ansi2freq(i+'#',k)
                    plt.axline((0,f),(1,f),lw=1,color='#FFC9C9')
                k+=1
            plt.xlim([snd.xmin, snd.xmax])
        if intn:
            plt.subplot(al*100+10+(3 if freq else 2))
            its = snd.to_intensity()
            iv = its.as_array()[0]
            plt.plot(its.xs(),iv)
            plt.xlim([snd.xmin, snd.xmax])
            plt.xlabel("time [s]")
            plt.show()

class AudioEdit:
    def __init__(self,r,a):
        self.r,self.a=r,a
    @classmethod
    def from_file(cls,fn):
        fn=filesuf(fn,'.wav')
        r,a=wav.read(fn)
        return cls(r,a)
    def __str__(self):
        return str(self.r)+'\n'+repr(self.a)
    __repr__=__str__
    def cut(self,fr,to=None):
        to=len(self.a) if to is None else int(to*self.r)+1
        self.a=self.a[int(fr*self.r):to]
        return self
    def mult(self,t):
        self.a=(self.a.astype(np.float64)*t).astype(self.a.dtype)
        return self
    def int32(self):
        if self.a.dtype==np.int16:
            self.a=self.a.astype(np.int32)
            self.a*=2**16
        return self
    def repeat(self,times,delay=0):
        if delay==0:
            delay=len(self.a)/self.r
        if len(self.a.shape)==2:
            res=np.zeros((self.a.shape[0]+int(delay*self.r*times),
                          self.a.shape[1]),dtype=self.a.dtype)
        else:
            res=np.zeros(self.a.shape[0]+int(delay*self.r*times),
                         dtype=self.a.dtype)
        for i in range(times):
            res[int(delay*i*self.r):
                self.a.shape[0]+int(delay*i*self.r)]+=self.a
        self.a=res
        return self
    def save(self,fn):
        fn=filesuf(fn,'.wav')
        wav.write(fn,self.r,self.a)
