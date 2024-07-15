from FIXED import *
class EQ(tk.Frame):
    pass
class Synthesizer(tk.Frame):
    def __init__(self,ops,graph
                 fixed=None,mul=1.0,
                 output=-20,env=Envelope(),
                 pitch=Envelope(0,0.001,0,0.001,0,0.001,0,0,0,0),
                 pitch_type='step',
                 filter=EQ()
                 ):
        pass

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
'''    
w=tk.Tk()
ic=imt.PhotoImage(im.open('icon.png'))
w.wm_iconphoto(True,ic)
w.title('FSWM v%s --by HYWY/FST/WWPE'%__version__)
w.geometry('1120x630+700+50')
w.resizable(0,0)
w.mainloop()
#'''
