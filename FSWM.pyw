from FIXED import *

class OneDSpectrogram(tk.Canvas):
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

A1=Synthesizer([Operator([i/100 for i in [86,100,100,86,86,86,86,71,
			  71,71,71,71,71,71,71,71,71,
			  57,57,57,57,57,57,57,57,57,
			  57,57]])],
               [[1,0]],
               output=0.05)
RES=np.zeros(44100*100)
RES[:4*44100]+=A1(Pitch(),4)
plt.ion()
plt.plot(RES)
RES=(RES*AMPL).astype(INT)
wav.write('test.wav',44100,RES)
#w.mainloop()
w.destroy()
#'''
