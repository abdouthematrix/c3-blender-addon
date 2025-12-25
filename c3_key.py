import struct

class C3Frame:
    def __init__(self):
        self.nFrame = 0
        self.fParam = [0.0]
        self.bParam = [False]
        self.nParam = [0]
    
    @staticmethod
    def read(file):
        frame = C3Frame()
        frame.nFrame = struct.unpack('<i', file.read(4))[0]
        frame.fParam[0] = struct.unpack('<f', file.read(4))[0]
        frame.bParam[0] = struct.unpack('<?', file.read(1))[0]
        file.read(3)
        frame.nParam[0] = struct.unpack('<i', file.read(4))[0]
        return frame

class C3Key:
    def __init__(self):
        self.dwAlphas = 0
        self.lpAlphas = None
        self.dwDraws = 0
        self.lpDraws = None
        self.dwChangeTexs = 0
        self.lpChangeTexs = None
    
    @staticmethod
    def Key_Clear(lpKey):
        lpKey.dwAlphas = 0
        lpKey.lpAlphas = None
        lpKey.dwDraws = 0
        lpKey.lpDraws = None
        lpKey.dwChangeTexs = 0
        lpKey.lpChangeTexs = None
    
    @staticmethod
    def Key_ProcessAlpha(lpKey, dwFrame, dwFrames):
        fReturn = 0.0
        
        sindex = -1
        eindex = -1
        
        for n in range(int(lpKey.dwAlphas)):
            if lpKey.lpAlphas[n].nFrame <= int(dwFrame):
                if sindex == -1 or n > sindex:
                    sindex = n
            if lpKey.lpAlphas[n].nFrame > int(dwFrame):
                if eindex == -1 or n < eindex:
                    eindex = n
        
        if sindex == -1 and eindex > -1:
            fReturn = lpKey.lpAlphas[eindex].fParam[0]
        elif sindex > -1 and eindex == -1:
            fReturn = lpKey.lpAlphas[sindex].fParam[0]
        elif sindex > -1 and eindex > -1:
            fReturn = lpKey.lpAlphas[sindex].fParam[0] + \
                      (float(dwFrame - lpKey.lpAlphas[sindex].nFrame) / float(lpKey.lpAlphas[eindex].nFrame - lpKey.lpAlphas[sindex].nFrame)) * \
                      (lpKey.lpAlphas[eindex].fParam[0] - lpKey.lpAlphas[sindex].fParam[0])
        else:
            return False, fReturn
        
        return True, fReturn
    
    @staticmethod
    def Key_ProcessDraw(lpKey, dwFrame):
        bReturn = False
        
        for n in range(int(lpKey.dwDraws)):
            if lpKey.lpDraws[n].nFrame == int(dwFrame):
                bReturn = lpKey.lpDraws[n].bParam[0]
                return True, bReturn
        
        return False, bReturn
    
    @staticmethod
    def Key_ProcessChangeTex(lpKey, dwFrame):
        nReturn = 0
        
        for n in range(int(lpKey.dwChangeTexs)):
            if lpKey.lpChangeTexs[n].nFrame == int(dwFrame):
                nReturn = lpKey.lpChangeTexs[n].nParam[0]
                return True, nReturn
        
        return False, nReturn
