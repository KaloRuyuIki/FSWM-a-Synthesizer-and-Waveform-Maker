#模块
import scipy.io.wavfile as wav
from scipy import fft
import matplotlib.pyplot as plt
import numpy as np
import parselmouth as prt
import os
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

#一些常数
__product__ = "FSWM: a Synthesizer & WAV-file Maker"
__version__ = "0.4.1"
PI=np.pi
TAU=2*np.pi
INT=np.int32
SRT=np.int8
AMPL=np.iinfo(INT).max
INF=float('inf')
NINF=-255

#预处理
plt.ion()
ctypes.windll.shcore.SetProcessDpiAwareness(1)
        
class FehError(Exception):
    '''The Exception of FSWM'''
    
class FreqCalcNum:
    def __init__(self,eqtp=12,do=0,do_oct=-1,A=440):
        """
        if eqpt==12:
            do=0  A 440
            do=3  C 
        """
        self.A=A
        self.e=eqtp
        if not 0<=do<eqtp:
            raise FehError("%d超过了%d平均律的范围" % (do,eqtp))
        self.do=A*2**(do/eqtp+do_oct)
    __repr__=__str__=lambda self:'(A=%.2f,do=%.2f,eq=%d)'%(self.A,
                                                           self.do,
                                                           self.e)
    def t2n(self,i,o=0):
        if not 0<=i<self.e:
            raise FehError("%d超过了%d平均律的范围" % (i,self.e))
        return o+i/self.e
    def n2f(self,n):
        return round(self.do*2**(n),10)
    def t2f(self,i,o=0):
        return self.n2f(self.t2n(i,o))
class FreqCalcANSI(FreqCalcNum):
    def __init__(self,notes,A=440):
        self.notes,self.C=notes,notes.index('C')
        super().__init__(len(notes),self.C,-1,A)
    def a2t(self,note,m=0):
        return (self.notes.index(note)-self.C)%len(self.notes),m
    def a2f(self,note,m=0):
        if note=='O':return 0
        return self.t2f(*self.a2t(note,m))
spfc={12:FreqCalcANSI(['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']),
      19:FreqCalcANSI(['A','A#','Bb','B','B#','C','C#','Db','D','D#',
                     'Eb','E','E#','F','F#','Gb','G','G#','Ab']),
      24:FreqCalcANSI(['A','A_','A#','Bd','B','B_','C','C_','C#','Dd','D','D_',
                       'D#','Ed','E','E_','F','F_','F#','Gd','G','G_','G#','Ad'])
      }
fc=spfc[12]

#大量的主代码
def dbtran(dB,base=1):
    return 10**(dB/20)*base
def revdb(n,base=1):
    return np.log10(n/base)*20
def make_db(a,b,l):
    return dbtran(np.linspace(a,b,l))
def make_line(a,b,l):
    return np.linspace(dbtran(a),dbtran(b),l)
def make_cubic(a,b,l):
    """
    formula:-(a-b)x^3+b
    """
    a,b=dbtran(a),dbtran(b)
    return np.linspace(-1,0,l)**3*-(a-b)+b
class FMeta(type):#一个将__repr__设为和__str__一样的元类
    def __new__(cls, name, bases, dict):
        dict['__repr__']=dict['__str__']
        return type.__new__(cls, name, bases, dict)
class Envelope(metaclass=FMeta):#包络
    def __init__(self,i=0,a=0,p=0,d=0,s=0,r=0,
                 ip=make_line,ps=make_cubic,sr=make_cubic):
        self.p=(i,a,p,d,s,r)
        self.f=(ip,ps,sr)
    def __str__(self):
        return ("Envelope(i=%.3fdB, a=%.3fs, p=%.3fdB, "
                "d=%.3fs, s=%.3fdB, r=%.3fs, "%self.p+
                "ip=%s, ps=%s, sr=%s)"%tuple(i.__name__ for i in self.f))
    def __call__(self,sec,tot=None,rate=44100):
        i,p,s=(self.p[0],self.p[2],self.p[4])
        a,d,r=(np.array((self.p[1],self.p[3],self.p[5]))*rate).astype(INT)
        ser=int(sec*rate)
        if tot is None or tot<sec+self.p[5]:#总时长不够就加
            tot=sec+self.p[5]
        tot=round(tot,10)
        ful=int(tot*rate)
        #print(tot,ful,sec,ser)
        X=np.zeros(ful)
        att=self.f[0](i,p,a)#起音->衰减
        dec=self.f[1](p,s,d)#衰减->延时
        if ser<a:#发音时长不足以起音
            X[:ser]=att[:ser]#截取
        else:
            X[:a]=att
            sed=ser-a
            if sed<d:#发音时长不足以衰减
                X[a:a+sed]=dec[:sed]
            else:
                X[a:a+d]=dec
                X[a+d:a+sed]=dbtran(s)#延时
        X[ser:ser+r]=self.f[2](s,NINF,r)#释放
        return X
class Filter(metaclass=FMeta):
    def __init__(self,typ=0,cen=0,rel=0,dif=0,env=Envelope()):
        self.t,self.c,self.r,self.d,self.e=typ,cen,rel,dif,env
    def __str__(self):
        return "Filter(%d, %.3f, %.3f, %.3f, %s)"%(self.t,self.c,self.r,
                                                   self.d,self.e)
    def getseqt1(self,frq,num,sec,tot=None,rate=44100):
        pass
    def getseqt2(self,frq,num,sec,tot=None,rate=44100):
        pass
    def __call__(self,frq,num,sec,tot=None,rate=44100):
        pass
class Operator(metaclass=FMeta):
    def __init__(self,frqs,output=-20,
                 freqmul=1,fixed=None,
                 flt=None,env=Envelope()):
        self.f,self.o,self.e=frqs,output,env
        self.fx,self.fm=fixed,freqmul
    def __str__(self):
        pref='['+', '.join('%.3f'%i for i in self.f)+']'
        return ('Operator('
                'frq=%s, '%pref+
                'output=%.3fdB ,'%self.o+
                'freqmul=%.3f, '%self.fm+
                'fixed=%s, '%(None if self.fx is None else "%.3fHz"%self.fx)+
                'env=%s)'%self.e)
    @property
    def rel(self):
        return self.e.p[5]
    def __call__(self,frq,sec,tot=None,fm=None,rate=44100):
        #频率相关
        if self.fx is not None:
            frq=self.fx
        frq*=self.fm
        
        see=round(sec+self.rel,10)#加上释放的时长
        ser=int((see)*rate)
        if tot is None or tot<see:#总时长不够就加
            tot=see
        tot=round(tot,10)
        ful=int(tot*rate)
        #print(tot,ful,see,ser)
        
        if fm is None:#没有可用于调频的
            fm=np.zeros(ful)
        else:
            if ful<len(fm):#调频的超出了目前可用的时间
                tot=len(fm)/rate
                ful=len(fm)
            else:#没达到
                ffm=np.zeros(ful)
                ffm[:len(fm)]=fm
                fm=ffm
                
        X=np.zeros(ful)
        X[:ser]=np.linspace(0,see,ser)
        #Add
        R=np.zeros(ful)
        for x,i in enumerate(self.f):
            R+=np.sin((x+1)*(TAU*X*frq+fm))*i
        R*=self.e(sec,tot,rate)*dbtran(self.o)
        return R
    @classmethod
    def formula(cls,f,items,*ag,**kw):
        return cls([f(i) for i in range(1,items+1)],*ag,**kw)
class Synthesizer(metaclass=FMeta):
    def __init__(self,op,gr):
        self.o,self.g=op,gr
        self.t=self.topo()
        if self.t:
            if self.t[-1]==0:
                self.rel=max(i.rel for i in self.o)
            else:
                raise FehError("结尾必须是0")
        else:
            raise FehError("有环")
    def topo(self):
        v,g=len(self.o)+1,self.g
        self.v=v
        a=[[] for i in range(v)]
        d=[0]*v
        for x,y in g:
            a[x].append(y)
            d[y]+=1
        q=[]
        for i in range(v):
            if d[i]==0:
                q.append(i)
        t=[]
        while len(q):
            i=q.pop(0)
            t.append(i)
            for j in a[i]:
                d[j]-=1
                if d[j]==0:
                    q.append(j)
        if not any(d):
            self.nex=a
            return t
    def __str__(self):
        return 'Synthesizer(%s, %s)'%(self.o,self.g)
    def __call__(self,frq,sec,rate=44100):
        tot=round(sec+self.rel,10)
        fms=np.zeros((self.v,int(tot*rate)))
        #print(self.t)
        for i in self.t[:-1]:
            r1=self.o[i-1](frq,sec,tot,fms[i],rate)
            for j in self.nex[i]:
                fms[j]+=r1
        return fms[0]
class Maker:
    def __init__(self,name,bpm=120,rate=44100):
        self.n,self.b,self.r=name,bpm,rate
        self.t=np.zeros((2,1))
    def write(self,tmb,frq,sec,dur,left=1,right=1):
        sec*=60/self.b
        dur*=60/self.b
        a=tmb(frq,dur)
        at=int(sec*self.r)
        al=at+len(a)
        bef=self.t.shape[1]
        if bef<al:
            self.t=np.concatenate((self.t,np.zeros((2,al-bef))),1)
        self.t[0,at:al]+=a*left
        self.t[1,at:al]+=a*right
    def save(self):
        wav.write(self.n,self.r,(self.t.T*AMPL).astype(INT))
squ=Operator.formula(lambda k:(0 if k%2==0 else 1/k),64,
                     output=-16,
                     )
sin=Operator([1],fixed=10,output=-10)
saw=Operator.formula(lambda k:1/k,64,output=3)
squ=Synthesizer([squ,sin],[(2,1),(1,0)]) 
m=Maker("Method.wav",125)
m.write(squ,fc.a2f("C#",+0),0,1)
m.write(squ,fc.a2f("A#",-1),1,1)
m.write(squ,fc.a2f("F",+0),2,2)
m.write(squ,fc.a2f("C#",+0),4,1)
m.write(squ,fc.a2f("A#",-1),5,0.5)
m.write(squ,fc.a2f("F",+0),5.5,2.5)
m.write(squ,fc.a2f("C#",+0),8,1)
m.write(squ,fc.a2f("A#",-1),9,1)
m.write(squ,fc.a2f("F",+0),10,2)
m.write(squ,fc.a2f("C#",+0),12,1)
m.write(squ,fc.a2f("A#",-1),13,0.5)
m.write(squ,fc.a2f("F",+0),13.5,2.5)
m.save()

