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

def dbtran(dB):
    return 10**(dB/20)
def revdb(n):
    return np.log10(n)*20
class Keyboard(tk.Canvas):
    def __init__(self,tet:int=12,a:float=440,
                 keyname:dict[str,dict]={},
                 highlight:dict[str,list]={},
                 master=None):
        if master is not None:
            super().__init__(master,background='#D7D8E0')
        self.t,self.a,self.k,self.h=tet,a,keyname,highlight
    def get(self,key,octave=0,tonic=0):
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
            if typ=='freq':
                v[sec]=cls.getx(env.i,env.p,env.a,sec,env.fip)
            elif typ=='step':
                v[sec]=cls.getx(env.i,env.p,env.a,sec,0)
            f.append(env.fse)
        elif sec<env.a+env.d:
            v[env.a]=env.p
            if typ=='freq':
                v[sec]=cls.getx(env.p,env.s,env.d,sec,env.fps)
            elif typ=='step':
                v[sec]=cls.getx(env.p,env.s,env.d,sec,0)
            f.extend([env.fps,env.fse])
        else:
            v[env.a],v[env.a+env.d],v[sec]=env.p,env.s,env.s
            f.extend([env.fps,0,env.fse])
        v[sec+env.r]=env.e
        f.append(0)
        return cls(v,f,typ)
    def __init__(self,
                 values:dict[float,float]={0:440,-1:440},
                 functions:list[int]=[1],
                 typ:str='freq',
                 tet=12):
        if typ=='freq':
            assert len(values)==len(functions)+1
        self.v,self.f,self.t=values,functions,typ
        self.tet=tet
    def __str__(self):
        return 'Pitch(%s, %s, %s)'%(self.v,self.f,self.t)
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
    def get(self,sec,tot,rate=44100):
        assert self.t=='freq'
        RES=np.zeros(int(rate*tot))
        D=self.v.copy()
        assert max(D)>sec
        D[sec]=D[-1]
        del D[-1]#替换结尾
        vl=sorted(D.keys())
        last=0
        for i in range(len(self.f)):
            bef,aft=vl[i],vl[i+1]
            bid,aid=int(rate*bef),int(rate*aid)
            bvl,avl=D[bef],D[aft]
            RES[bid:aid]=self.chirp(bvl,avl,aft-bef,aid-bid,i)+last
            last=RES[aid-1]
        return RES
    def __add__(self,other):
        '''
        {0:400,100:600,200:200,-1:400},[0,1,2]
        {0:0,50:2,150:-2,200:2,300:-1,-1:-3},typ='step'

        0,0 -> 0:400*2^(0/12)                       []  
        1,1 -> 50:intp(400,600,100,50,0)*2^(2/12)   [0] 1
        1,2 -> 100:600*2^(intp(-2,2,100,50,0)/12)   [0] 2
        2,2 -> 150:intp(600,200,100,50,1)*2^(-2/12) [1] 1
        2,3 -> 200:200*2^(2/12)                     [1] 5
        3,4 -> 300:200*2^(-1/12)                    [2] 4
        3,5 -> -1:400^2^(-3/12)                     [2] 5

        {0:0, 4:2,8:-2,9:-3,-1:1},typ='step'
        {0:-1,2:1,6:-4,8:7, -1:4},typ='step'
        0,0 -> 0:-1
        1,1 -> 2:(0,2,4,2,0)+1  1
        1,2 -> 4:(1,-4,4,2,0)+2 2
        2,2 -> 6:(-2,2,4,2,0)-4 1
        2,3 -> 8:-2+7           5
        3,4 -> 9:-3+7           3
        4,4 -> -1:5             5
        '''
        if self.t=='freq' and other.t=='step':
            D1,D2=self.v,other.v
            K1,K2=sorted(D1.keys())[1:]+[-1],sorted(D2.keys())[1:]+[-1]
            l1,l2=len(D1),len(D2)
            i1,i2=1,1
            RES={0:D1[0]*2**(D2[0]/other.tet)}
            FUN=[]
            TET=other.tet
            while i1<l1 and i2<l2:
                k1,k2,j1,j2=K1[i1],K2[i2],K1[i1-1],K2[i2-1]#时间点
                d1,d2,c1,c2=D1[k1],D2[k2],D1[j1],D2[j2]#旧值
                FUN.append(self.f[i1-1])
                if k1>k2:
                    if k2==-1:#3
                        RES[k1]=d1*2**(c2/TET)
                        i1+=1
                    else:#1
                        RES[k2]=self.getx(c1,d1,k1-j1,k2-j1,self.f[i1-1])*2**(d2/TET)
                        i2+=1
                elif k1<k2:
                    if k1==-1:#4
                        RES[k2]=c1*2**(d2/TET)
                        i2+=1
                    else:#2
                        RES[k1]=d1*2**(self.getx(c2,d2,k2-j2,k1-j2,0)/TET)
                        i1+=1
                else:#5
                    RES[k1]=d1*2**(d2/TET)
                    i1+=1
                    i2+=1
            return Pitch(RES,FUN)
        elif self.t=='step' and other.t=='freq':
            return other+self
        elif self.t==other.t=='step':
            D1,D2=self.v,other.v
            K1,K2=sorted(D1.keys())[1:]+[-1],sorted(D2.keys())[1:]+[-1]
            l1,l2=len(D1),len(D2)
            i1,i2=1,1
            RES={0:D1[0]*2**(D2[0]/other.tet)}
            FUN=[]
            TET=other.tet
            while i1<l1 and i2<l2:
                k1,k2,j1,j2=K1[i1],K2[i2],K1[i1-1],K2[i2-1]#时间点
                d1,d2,c1,c2=D1[k1],D2[k2],D1[j1],D2[j2]#旧值
                if k1>k2:
                    if k2==-1:#3
                        RES[k1]=d1+c2
                        i1+=1
                    else:#1
                        RES[k2]=self.getx(c1,d1,k1-j1,k2-j1,0)+d2
                        i2+=1
                elif k1<k2:
                    if k1==-1:#4
                        RES[k2]=c1+d2
                        i2+=1
                    else:#2
                        RES[k1]=d1+self.getx(c2,d2,k2-j2,k1-j2,0)
                        i1+=1
                else:#5
                    RES[k1]=d1+d2
                    i1+=1
                    i2+=1
            return Pitch(RES,FUN,'step')
        elif self.t==other.t=='freq':
            return PitchGroup(self,other)
        return NotImplemented
class PitchGroup:
    def __init__(self,*args):
        assert all(i.t=='freq' for i in args)
        self.p=args
        self.t='group'
    def get(self,sec,tot,rate=44100):
        RES=np.zeros(int(rate*tot))
        for i in self.p:
            RES+=i.get(sec,tot,rate)
        return RES
    def __add__(self,other):
        if other.t=='group':
            return PitchGroup(*self.p,*other.p)
        elif other.t=='freq':
            return PitchGroup(*self.p,other.p)
        else:
            return PitchGroup(*(i+other for i in self.p))
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
    def get(self,sec,tot,rate=44100):
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
                 output=-20,env=Envelope(),
                 phase=0,feedback=0):
        self.fq,self.fc=freqs,func
        self.fx,self.m=fixed,mul
        self.o,self.e=output,env
        self.ph,self.fd=phase,feedback
        self.p,self.pt=pitch,pitch_type
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
            pit=Pitch({0:self.fx,-1:self.fx},[0])
        X=pit.get(sec,tot)*self.m
        for x,i in enumerate(self.fq):
            RES+=self.fc(TAU*((x+1)*X+fm+self.ph))*i
        return RES*self.e.get(sec,tot,rate)*self.o
    @classmethod
    def formula(cls,name,length,**kwargs):
        return cls([cls.form[name](i) for i in range(1,length+1)],
                   **kwargs)
