####模块导入####
import numpy as np#掌管数据的神
import scipy.io.wavfile as wav#掌管读取和写入的神
import scipy.signal as ssg#掌管信号处理的神
import tkinter as tk#掌管窗口的基础
#from tkinter import filedialog as fd,messagebox as mb,ttk
from PIL import Image as im,ImageTk as imt,ImageColor as imc
import ctypes#掌管分辨率的神
import regex as re#掌管正则表达式的神
import matplotlib.pyplot as plt#掌管显示的废物
import json#掌管JSON的神
import windnd as wd#掌管文件拖入的神
import os.path as pt#掌管文件处理的神
import pygame.midi as pmd#掌管键盘的神
from pydub import AudioSegment as auds

__version__ = "0.1"
PI=np.pi
TAU=2*np.pi
INT=np.int32
AMPL=np.iinfo(INT).max
NINF=-255
FONT=('微软雅黑',14)
FONT2=('微软雅黑',10)
#plt.ion()
#pmd.init()
ctypes.windll.shcore.SetProcessDpiAwareness(1)
w=tk.Tk()
ic=imt.PhotoImage(im.open('icon.png'))
w.wm_iconphoto(True,ic)
w.title('FSWM v%s --by HYWY/FST/WWPE'%__version__)
w.geometry('800x600+50+50')
w.resizable(0,0)

def dbtran(dB):
    return 10**(dB/20)
def revdb(n):
    return np.log10(n)*20
class Keyboard(tk.Canvas):
    def __init__(self,tet:int=12,a:float=440,
                 keyname:dict[str,dict]={},
                 highlight:dict[str,list]={},
                 master=None):
        self.t,self.a,self.k,self.h=tet,a,keyname,highlight
    def __call__(self,key,octave=0,tonic=0):
        return self.a*2**((key+tonic)/self.t+octave)
    def obj(self):
        return {'tet':self.t,'a':self.a,'keyname':self.k,'highlight':self.h}
class Pitch:
    @staticmethod
    def getx(a,b,c,x,f):
        match f:
            case 0:
                return (a-b)/c*x+a
            case 1:
                return (b-a)*((x-c)/c)**3+b
            case 2:
                return 2**(x/c)+2*a-b
    @classmethod
    def from_env(cls,env,sec,typ):
        assert env.d!=0
        assert env.r!=0
        v,f={0:env.i,-1:env.e},[env.fip]
        if sec<env.a:
            v[sec]=cls.getx(env.i,env.p,env.a,sec,env.fip)
            f.append(env.fse)
        elif sec<env.a+env.d:
            v[env.a]=env.p
            v[sec]=cls.getx(env.p,env.s,env.d,sec,env.fps)
            f.extend([env.fps,env.fse])
        else:
            v[env.a],v[env.a+env.d],v[sec]=env.p,env.s,env.s
            f.extend([env.fps,0,env.fse])
        v[sec+env.r]=env.e
        f.append(0)
        return cls(v,f,typ)
    def __init__(self,
                 values:dict[float,float]={0:440,-1:440},
                 functions:list[int]=[1]):
        assert len(values)==len(functions)+1
        self.v,self.f=values,functions
    def __str__(self):
        return 'Pitch(%s, %s)'%(self.v,self.f)
    __repr__=__str__
    def chirp(self,a,b,s,l,i):
        match self.f[i]:
            case 0:#直线滑音曲线
                X=np.linspace(0,s,l)
                return ((-1/2*a+1/2*b)*X**2+a*s*X)/s
            case 1:#三次滑音曲线
                X=np.linspace(0,s,l)
                return ((-1/4*a+1/4*b)*X**4+
                       (a-b)*s*X**3+
                       (-3/2*a+3/2*b)*s**2*X**2+
                       a*s**3*X)/s**3
            case 2:#指数滑音曲线
                if b<a:
                    return self.chirp(b,a,s,l,i)[::-1]
                X=np.linspace(0,s,l)
                return ((b-a)*2**(X/s)*s+X*np.log(2)*(2*a-b))/np.log(2)
    def __call__(self,sec,tot,rate=44100):
        RES=np.zeros(int(rate*tot))
        D=self.v.copy()
        assert max(D)<sec
        D[sec]=D[-1]
        del D[-1]#替换结尾
        vl=sorted(D.keys())
        last=0
        for i in range(len(self.f)):
            bef,aft=vl[i],vl[i+1]
            bid,aid=int(rate*bef),int(rate*aft)
            bvl,avl=D[bef],D[aft]
            RES[bid:aid]=self.chirp(bvl,avl,aft-bef,aid-bid,i)+last
            last=RES[aid-1]
        return RES
class Envelope(tk.Frame):
    '''
    a=Envelope(-255,0.2,0,1,-6,0.5)
    plt.plot(a.get(0.1,5))
    plt.plot(a.get(0.2,5))
    plt.plot(a.get(0.8,5))
    plt.plot(a.get(1.2,5))
    plt.plot(a.get(4.1,5))
    '''
    @staticmethod
    def interpolate(a,b,l,f):
        match f:
            case 0:
                return np.linspace(a,b,l)
            case 1:
                return np.linspace(-1,0,l)**3*(b-a)+b
            case 2:
                return 2**np.linspace(0,1,l)*(b-a)+2*a-b
    def __init__(self,i=1,a=0,p=1,d=0,s=1,r=0,e=0,
                 fip=0,fps=1,fse=1):
        self.i,self.p,self.s,self.e=i,p,s,e
        self.a,self.d,self.r=a,d,r
        self.fip,self.fps,self.fse=fip,fps,fse
    def __call__(self,sec,tot,rate=44100):
        RES=np.zeros(int(tot*rate))
        S=int(sec*rate)
        A,D,R=int(self.a*rate),int(self.d*rate),int(self.r*rate)
        AD=self.interpolate(self.i,self.p,A,self.fip)
        DS=self.interpolate(self.p,self.s,D,self.fps)
        if S<A:
            RES[0:S]=AD[0:S]
            RES[S:S+R]=self.interpolate(AD[S],0,R,self.fse)
        else:
            RES[0:A]=AD
            if S-A<D:
                RES[A:S]=DS[0:S-A]
                RES[S:S+R]=self.interpolate(DS[S-A],0,R,self.fse)
            else:
                RES[A:A+D]=DS
                RES[A+D:S]=np.ones(S-A-D)*self.s
                RES[S:S+R]=self.interpolate(self.s,self.e,R,self.fse)
        return RES
class Operator(tk.Frame):
    form={'square':lambda k:0 if k%2==0 else 1/k*4/PI,
          'saw':lambda k:1/k*2/PI,
          'triangle':lambda k:0 if k%2==0 else (-1)**((k+1)//2)/(k**2)*8/PI**2,
          'sin':lambda k:1 if k==1 else 0,
          }
    def __init__(self,freqs,func=np.sin,
                 fixed=None,mul=1.0,
                 output=1,env=Envelope(),
                 phase=0,feedback=0):
        self.fq,self.fc=freqs,func
        self.fx,self.m=fixed,mul
        self.o,self.e=output,env
        self.ph,self.fd=phase,feedback
    def __call__(self,pit,sec,tot=None,fm=None,feed=True,rate=44100):
        if tot is None:
            tot=sec+self.e.r
        LEN=int(tot*rate)
        RES=np.zeros(LEN)
        if fm is None:
            fm=np.zeros(LEN)
        if feed:
            fm+=self(pit,sec,tot,fm,False,rate)*self.fd
        if self.fx:
            pit=Pitch({0:self.fx,-1:self.fx},[0])
        X=pit(sec,tot)*self.m
        for x,i in enumerate(self.fq):
            RES+=self.fc(TAU*((x+1)*X+fm+self.ph))*i
        return RES*self.e(sec,tot,rate)*self.o
    @classmethod
    def formula(cls,name,length,**kwargs):
        return cls([cls.form[name](i) for i in range(1,length+1)],
                   **kwargs)
class FFT_EQ(tk.Frame):
    def __init__(self,*para:tuple[int,float,float]):
        self.p=para
    def __call__(self,arr,rate=44100):
        for t,c,g in self.p:
            if t in (0,1,2,3):
                []
class Synthesizer(tk.Frame):
    def __init__(self,ops,graph,
                 output=1,env=Envelope(),
                 filt=FFT_EQ()):
        self.op=ops
        self.rel=max(*(i.e.r for i in ops),env.r)
        self.gr=graph
        self.topo()
        self.o,self.e=output,env
        self.f=filt
    def topo(self):
        self.v=v=len(self.op)+1
        IND=[0]*(v)
        self.nex=NEX=[[] for i in range(v)]
        for x,y in self.gr:
            NEX[x].append(y)
            IND[y]+=1
        q=[]
        for x,i in enumerate(IND):
            if i==0:
                q.append(x)
        self.tp=t=[]
        while len(q):
            i=q.pop()
            t.append(i)
            for j in NEX[i]:
                IND[j]-=1
                if IND[j]==0:
                    q.append(j)
        assert not any(IND)
        assert t[-1]==0
    def __call__(self,pit,sec,rate=44100):
        tot=sec+self.rel
        FM=np.zeros((self.v,int(tot*rate)))
        for i in self.tp[:-1]:
            R=self.op[i-1](pit,sec,tot,FM[i],rate=rate)
            for j in self.nex[i]:
                FM[j]+=R
        return FM[0]*self.e(sec,tot,rate)*self.o
__all__=list(globals().keys())
