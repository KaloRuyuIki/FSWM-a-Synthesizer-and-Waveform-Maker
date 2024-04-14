from store import *
"""
构想：

"""
NINF=-255
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
                 ip=make_line,ps=make_db,sr=make_cubic):
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
        ful=int(tot*rate)
        X=np.zeros(ful)
        att=self.f[0](i,p,a)#起音->衰减
        dec=self.f[1](p,s,d)#衰减->延时
        if ser<a:#发音时长不足以起音
            X[:ser]=att[:ser]#截取
        else:
            X[:a]=att
            sed=ser-a
            if ser<d:#发音时长不足以衰减
                X[a:a+sed]=dec[:sed]
            else:
                X[a:a+d]=dec
                X[a+d:a+sed]=dbtran(s)#延时
        X[ser:ser+r]=self.f[2](s,NINF,r)#释放
        return X
class Filter(metaclass=FMeta):
    def __init__(self,t,c,r,d,e=Envelope()):
        self.t,self.c,self.r,self.d,self.e=t,c,r,d,e
    def __str__(self):
        return "Filter(%d, %.3f, %.3f, %.3f, %s)"%(self.t,self.c,self.r,
                                                   self.d,self.e)
    def __call__(self,sec,tot=None,rate=44100):
        pass
class Operator(metaclass=FMeta):
    def __init__(self,frq,output=-20,env=Envelope()):
        self.f,self.o,self.e=frq,output,env
    def __str__(self):
        pref='['+', '.join('%.3f'%i for i in self.f)+']'
        return ('Operator('
                'frq=%s,'%pref+
                'output=%.3fdB,'%self.o+
                'env=%s)'%self.e)
    def __call__(self,frq,sec,tot=None,fm=None,rate=44100):
        see=sec+self.e.p[5]#加上释放的时长
        ser=int((see)*rate)
        if tot is None or tot<sec:#总时长不够就加
            tot=sec
        ful=int(tot*rate)
        if fm is None:#没有可用于调频的
            fm=np.zeros(ful)
        X=np.zeros(ful)
        X[:ser]=np.linspace(0,see,ser)
        #Add
        R=np.zeros(ful)
        for x,i in enumerate(self.f):
            R+=np.sin(x*(TAU*X*frq+fm))*i
        R*=self.e(sec,tot)*dbtran(self.o)
        return R
    @classmethod
    def formula(cls,f,items,*ag,**kw):
        return cls([f(i) for i in range(0,items+1)],*ag,**kw)
a=Operator.formula(lambda k:(0 if k%2==0 else 1/k),64,
                   env=Envelope(NINF,0 ,0,1,-6,1))
b=Operator.formula(lambda k:1,1,env=Envelope(NINF,1,0,1,-6,2.5))
b2=Operator.formula(lambda k:1,1,output=0)
c=Operator.formula(lambda k:1,1,output=0,env=Envelope(NINF,2,20,1,7,1))

sec,tot=4,7
r=a(440,sec,tot,c(440,sec,tot))
wav.write("Env041.wav",44100,(r*AMPL).astype(INT))
'''
plt.subplots()
plt.plot(np.linspace(0,tot,int(tot*44100)),r)
plt.show()
#'''
