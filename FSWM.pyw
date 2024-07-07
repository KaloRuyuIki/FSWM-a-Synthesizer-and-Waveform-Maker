####模块导入####
import numpy as np#掌管数据的神
import scipy.io.wavfile as wav#掌管读取和写入的神
import scipy.signal as ssg#掌管信号处理的神
import tkinter as tk#掌管窗口的基础
from tkinter import filedialog as fd,messagebox as mb,ttk
from PIL import Image as im,ImageTk as imt,ImageColor as imc
import ctypes#掌管分辨率的神
import regex as re#掌管正则表达式的神
import matplotlib.pyplot as plt#掌管显示的废物
import json#掌管JSON的神
import windnd as wd#掌管文件拖入的神
import os.path as pt#掌管文件处理的神
import pygame.midi as pmd#掌管键盘的神

__version__ = "0.1"
PI=np.pi
TAU=2*np.pi
INT=np.int32
AMPL=np.iinfo(INT).max
NINF=-255
FONT=('微软雅黑',14)
FONT2=('微软雅黑',10)
plt.ion()
pmd.init()
ctypes.windll.shcore.SetProcessDpiAwareness(1)
def dbtran(dB):
    return 10**(dB/20)
def revdb(n):
    return np.log10(n)*20
class Keyboard(tk.Canvas):
    def __init__(self,master,jobj,mode=1,tone=0):
        super().__init__(master,background='#D7D8E0')
class Pitch:
    '''
    a=Pitch(3,[1,2,3],440,[220,880,440],440,1)
    wav.write('chirp1.wav',44100,(AMPL*np.sin(a.get(4)*TAU)).astype(INT))
    wav.write('chirp2.wav',44100,(AMPL*np.sin(a.get(7)*TAU)).astype(INT))
    '''
    def __init__(self,num,stamp,beg,value,end,func):
        self.n,self.s,self.v,self.f=num,stamp,value,func
        self.b,self.e=beg,end
    def chirp(self,a,b,s,l):
        match self.f:
            case 1:#三次滑音曲线
                X=np.linspace(0,s,l)
                return ((-1/4*a+1/4*b)*X**4+
                       (a-b)*s*X**3+
                       (-3/2*a+3/2*b)*s**2*X**2+
                       a*s**3*X)/s**3
            case 2:#直线滑音曲线
                X=np.linspace(0,s,l)
                return ((-1/2*a+1/2*b)*X**2+a*s*X)/s
            case 3:#指数滑音曲线
                if b<a:
                    return self.chirp(b,a,s,l)[::-1]
                X=np.linspace(0,s,l)
                return ((-2**(X/s)*a+2**(X/s)*b)*s+
                        X*np.log(2)*(2*a-b))/np.log(2)
    def get(self,sec,tot,rate=44100):
        LEN=int(tot*rate)
        RES=np.zeros(LEN)
        btr=sec if self.n==0 else self.s[0]
        bst=int(btr*rate)
        bvl=self.e if self.n==0 else self.v[0]
        RES[:bst]=self.chirp(self.b,bvl,btr,bst)
        last=RES[bst-1]
        for i in range(self.n-1):
            atr,btr=self.s[i],self.s[i+1]
            ast,bst=int(atr*rate),int(btr*rate)
            avl,bvl=self.v[i],self.v[i+1]
            RES[ast:bst]=self.chirp(avl,bvl,btr-atr,bst-ast)+last
            last=RES[bst-1]
        atr,btr=0 if self.n==0 else self.s[self.n-1],sec
        ast,bst=int(atr*rate),int(btr*rate)
        avl,bvl=self.b if self.n==0 else self.v[self.n-1],self.e
        RES[ast:bst]=self.chirp(avl,bvl,btr-atr,bst-ast)+last
        RES[bst:LEN]=self.chirp(bvl,bvl,tot-btr,LEN-bst)+RES[bst-1]
        return RES
class Envelope(tk.Canvas):
    '''
    a=Envelope(-255,0.2,0,1,-6,0.5)
    plt.plot(a.get(0.1,5))
    plt.plot(a.get(0.2,5))
    plt.plot(a.get(0.8,5))
    plt.plot(a.get(1.2,5))
    plt.plot(a.get(4.1,5))
    '''
    @staticmethod
    def cubic(a,b,l):
        return np.linspace(-1,0,l)**3*(b-a)+b
    def __init__(self,i=1,a=0,p=1,d=0,s=1,r=0,e=0):
        self.i,self.p,self.s,self.e=i,p,s,e
        self.a,self.d,self.r=a,d,r
    def get(self,sec,tot,rate=44100):
        RES=np.zeros(int(tot*rate))
        S=int(sec*rate)
        A,D,R=int(self.a*rate),int(self.d*rate),int(self.r*rate)
        AD=np.linspace(self.i,self.p,A)
        DS=self.cubic(self.p,self.s,D)
        if S<A:
            RES[0:S]=AD[0:S]
            RES[S:S+R]=self.cubic(AD[S],0,R)
        else:
            RES[0:A]=AD
            if S-A<D:
                RES[A:S]=DS[0:S-A]
                RES[S:S+R]=self.cubic(DS[S-A],0,R)
            else:
                RES[A:A+D]=DS
                RES[A+D:S]=np.ones(S-A-D)*self.s
                RES[S:S+R]=self.cubic(self.s,self.e,R)
        return RES
class EQ(tk.Frame):
    pass
class Filter(tk.Frame):
    pass
class OneDSpectrogram(tk.Canvas):
    pass
class Operator(tk.Frame):
    form={'square':lambda k:0 if k%2==0 else 1/k*4/PI,
          'saw':lambda k:1/k*2/PI,
          'triangle':lambda k:0 if k%2==0 else (-1)**((k+1)//2)/(k**2)*8/PI**2,
          'sin':lambda k:1 if k==1 else 0,
          }
    def __init__(self,freqs,func=np.sin,
                 fixed=None,mul=1.0,
                 output=-20,env=Envelope(),
                 phase=0,feedback=0):
        self.fq,self.fc=freqs,func
        self.fx,self.m=fixed,mul
        self.o,self.e=output,env
        self.ph,self.fd=phase,feedback
    def get(self,pit,sec,tot=None,fm=None,feed=True,rate=44100):
        if tot is None:
            tot=sec+self.e.r
        LEN=int(tot*rate)
        RES=np.zeros(LEN)
        if fm is None:
            fm=np.zeros(LEN)
        if feed:
            fm+=self.get(pit,sec,tot,fm,False,rate)*self.fd
        if self.fx:
            pit=Pitch(0,[],self.fx,[],self.fx)
        X=pit.get(sec,tot)*self.m
        for x,i in enumerate(self.fq):
            RES+=self.fc(TAU*((x+1)*X+fm+self.ph))*i
        return RES*self.e.get(sec,tot,rate)*self.o
    @classmethod
    def formula(cls,name,length,*args,**kwargs):
        return cls([cls.form[name](i) for i in range(1,length+1)],*args,**kwargs)
a=Operator([1],
           output=0.5,
           env=Envelope(0,0.001,dbtran(0),1,dbtran(-12),0.05),
           feedback=0)
p=Pitch(0,[],160,[],42,1)
wav.write('drum1.wav',44100,(AMPL*a.get(p,0.5,1)).astype(INT))

class Synthesizer(tk.Frame):
    def __init__(self):
        pass
class TonicSpectrogram(tk.Frame):
    pass
class AtonicSpectrogram(tk.Frame):
    pass

class TetkEditCanvas(tk.Canvas):
    def __init__(self,master,impt,length,keybd,inst,note):
        super().__init__(master,background='#D7D8E0')
class RealEditCanvas(tk.Canvas):
    pass
class RatioEditCanvas(tk.Canvas):
    pass
class Axis(tk.Canvas):
    def __init__(self,master,impt,length):
        super().__init__(master,background="#3F5866")
class NormalBlock(tk.Frame):
    def __init__(self,master,impt=(120,4,4),length=(10,0,0),begin=(0,0,0),
                 keybd=None,inst=None,note=None):
        super().__init__(master)
'''    
w=tk.Tk()
ic=imt.PhotoImage(im.open('icon.png'))
w.wm_iconphoto(True,ic)
w.title('FSWM v%s --by HYWY/FST/WWPE'%__version__)
w.geometry('1120x630+700+50')
w.resizable(0,0)
w.mainloop()
#'''
