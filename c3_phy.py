import struct
from mathutils import Vector, Matrix
from . import c3_main
from . import c3_common
from . import c3_key
from . import c3_motion

_BONE_MAX_ = 2
_MORPH_MAX_ = 4

class PhyVertex:
    def __init__(self, morphMax, boneMax):
        self.pos = [Vector((0, 0, 0)) for _ in range(morphMax)]
        self.TexCoord = Vector((0, 0))
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.index = [0] * boneMax
        self.weight = [0.0] * boneMax

class PhyOutVertex:
    def __init__(self):
        self.Position = Vector((0, 0, 0))
        self.Color = (1.0, 1.0, 1.0, 1.0)
        self.TexCoord = Vector((0, 0))

class C3Phy:
    def __init__(self):
        self.lpName = None
        self.dwBlendCount = 0
        self.dwNVecCount = 0
        self.dwAVecCount = 0
        self.lpVB = None
        self.outputVertices = None
        self.dwNTriCount = 0
        self.dwATriCount = 0
        self.lpIB = None
        self.lpTexName = None
        self.nTex = -1
        self.nTex2 = -1
        self.bboxMin = Vector((0, 0, 0))
        self.bboxMax = Vector((0, 0, 0))
        self.lpMotion = None
        self.fA = 1.0
        self.fR = 1.0
        self.fG = 1.0
        self.fB = 1.0
        self.Key = c3_key.C3Key()
        self.bDraw = True
        self.dwTexRow = 1
        self.InitMatrix = Matrix.Identity(4)
        self.uvstep = Vector((0, 0))
        self.m_dwPhyNum = 0
        self.m_phy = [None] * 16
    
    @staticmethod
    def Phy_Clear(lpPhy):
        lpPhy.lpName = None
        lpPhy.dwBlendCount = 0
        lpPhy.dwNVecCount = 0
        lpPhy.dwAVecCount = 0
        lpPhy.lpVB = None
        lpPhy.outputVertices = None
        lpPhy.dwNTriCount = 0
        lpPhy.dwATriCount = 0
        lpPhy.lpIB = None
        lpPhy.lpTexName = None
        lpPhy.nTex = -1
        lpPhy.nTex2 = -1
        lpPhy.bboxMin = Vector((0, 0, 0))
        lpPhy.bboxMax = Vector((0, 0, 0))
        lpPhy.lpMotion = None
        lpPhy.fA = lpPhy.fR = lpPhy.fG = lpPhy.fB = 1.0
        lpPhy.Key = c3_key.C3Key()
        c3_key.C3Key.Key_Clear(lpPhy.Key)
        lpPhy.bDraw = True
        lpPhy.dwTexRow = 1
        lpPhy.uvstep = Vector((0, 0))
        lpPhy.InitMatrix = Matrix.Identity(4)
    
    def C3_Load(self, lpName):
        self.m_dwPhyNum = 0
        for n in range(16):
            self.m_phy[n] = None
        
        try:
            with open(lpName, 'rb') as file:
                version = file.read(16).decode().rstrip('\0')
                
                if version != c3_main.C3_VERSION:
                    return False
                
                while file.tell() < len(open(lpName, 'rb').read()):
                    chunk = c3_common.ChunkHeader.read(file)
                    if chunk.byChunkID == b'PHY ' or chunk.byChunkID == b'PHY3' or chunk.byChunkID == b'PHY4':
                        result, phy = C3Phy.Phy_Load(file, chunk.ChunkID)
                        if not result:
                            break
                        self.m_phy[self.m_dwPhyNum] = phy
                        self.m_dwPhyNum += 1
                    else:
                        file.seek(chunk.dwChunkSize, 1)
        except Exception as e:
            print("Error:", e)
            return False
        
        return self.m_dwPhyNum > 0
    
    @staticmethod
    def Phy_Load(file, ChunkID, bTex=False):
        lpPhy = C3Phy()
        C3Phy.Phy_Clear(lpPhy)
        
        temp = struct.unpack('<I', file.read(4))[0]
        lpPhy.lpName = file.read(temp).decode().rstrip('\0')
        
        lpPhy.dwBlendCount = struct.unpack('<I', file.read(4))[0]
        lpPhy.dwNVecCount = struct.unpack('<I', file.read(4))[0]
        lpPhy.dwAVecCount = struct.unpack('<I', file.read(4))[0]
        
        totalVerts = lpPhy.dwNVecCount + lpPhy.dwAVecCount
        lpPhy.lpVB = []
        lpPhy.outputVertices = []
        
        morph_max = _MORPH_MAX_
        if ChunkID == "PHY3" or ChunkID == "PHY4":
            morph_max = 1
        
        for i in range(totalVerts):
            vert = PhyVertex(morph_max, _BONE_MAX_)
            
            for m in range(morph_max):
                x = struct.unpack('<f', file.read(4))[0]
                y = struct.unpack('<f', file.read(4))[0]
                z = struct.unpack('<f', file.read(4))[0]
                vert.pos[m] = Vector((x, y, z))
            
            u = struct.unpack('<f', file.read(4))[0]
            v = struct.unpack('<f', file.read(4))[0]
            vert.TexCoord = Vector((u, v))
            
            file.read(4)
            vert.color = (1.0, 1.0, 1.0, 1.0)
            
            for b in range(_BONE_MAX_):
                vert.index[b] = struct.unpack('<I', file.read(4))[0]
            
            for b in range(_BONE_MAX_):
                vert.weight[b] = struct.unpack('<f', file.read(4))[0]
            
            if ChunkID == "PHY3":
                x = struct.unpack('<f', file.read(4))[0]
                y = struct.unpack('<f', file.read(4))[0]
                z = struct.unpack('<f', file.read(4))[0]
            
            lpPhy.lpVB.append(vert)
            lpPhy.outputVertices.append(PhyOutVertex())            
            lpPhy.outputVertices[i].Position = vert.pos[0]
            lpPhy.outputVertices[i].Color = vert.color
            lpPhy.outputVertices[i].TexCoord = vert.TexCoord
        
        lpPhy.dwNTriCount = struct.unpack('<I', file.read(4))[0]
        lpPhy.dwATriCount = struct.unpack('<I', file.read(4))[0]
        
        totalIndices = (lpPhy.dwNTriCount + lpPhy.dwATriCount) * 3
        lpPhy.lpIB = []
        for i in range(totalIndices):
            lpPhy.lpIB.append(struct.unpack('<H', file.read(2))[0])
        
        temp = struct.unpack('<I', file.read(4))[0]
        lpPhy.lpTexName = file.read(temp).decode('gbk').rstrip('\0')
        
        x = struct.unpack('<f', file.read(4))[0]
        y = struct.unpack('<f', file.read(4))[0]
        z = struct.unpack('<f', file.read(4))[0]
        lpPhy.bboxMin = Vector((x, y, z))
        
        x = struct.unpack('<f', file.read(4))[0]
        y = struct.unpack('<f', file.read(4))[0]
        z = struct.unpack('<f', file.read(4))[0]
        lpPhy.bboxMax = Vector((x, y, z))
        
        lpPhy.InitMatrix = C3Phy.ReadMatrix(file)
        lpPhy.dwTexRow = struct.unpack('<I', file.read(4))[0]
        
        lpPhy.Key.dwAlphas = struct.unpack('<I', file.read(4))[0]
        lpPhy.Key.lpAlphas = []
        for i in range(lpPhy.Key.dwAlphas):
            lpPhy.Key.lpAlphas.append(c3_key.C3Frame.read(file))
        
        lpPhy.Key.dwDraws = struct.unpack('<I', file.read(4))[0]
        lpPhy.Key.lpDraws = []
        for i in range(lpPhy.Key.dwDraws):
            lpPhy.Key.lpDraws.append(c3_key.C3Frame.read(file))
        
        lpPhy.Key.dwChangeTexs = struct.unpack('<I', file.read(4))[0]
        lpPhy.Key.lpChangeTexs = []
        for i in range(lpPhy.Key.dwChangeTexs):
            lpPhy.Key.lpChangeTexs.append(c3_key.C3Frame.read(file))
        
        flag = file.read(4)
        if flag == b'STEP':
            lpPhy.uvstep.x = struct.unpack('<f', file.read(4))[0]
            lpPhy.uvstep.y = struct.unpack('<f', file.read(4))[0]
        else:
            file.seek(-4, 1)
        
        flag2 = file.read(4)
        if flag2 == b'2SID':
            pass
        else:
            file.seek(-4, 1)
        
        C3Phy.Phy_SetColor(lpPhy, 1, 1, 1, 1)
        
        return True, lpPhy
    
    @staticmethod
    def ReadMatrix(file):
        m = []
        for i in range(16):
            m.append(struct.unpack('<f', file.read(4))[0])
        return Matrix((
            (m[0], m[1], m[2], m[3]),
            (m[4], m[5], m[6], m[7]),
            (m[8], m[9], m[10], m[11]),
            (m[12], m[13], m[14], m[15])
        ))
    
    @staticmethod
    def Phy_Unload(lpPhy):
        lpPhy.lpName = None
        lpPhy.lpVB = None
        lpPhy.outputVertices = None
        lpPhy.lpIB = None
        lpPhy.lpTexName = None
        lpPhy.Key.lpAlphas = None
        lpPhy.Key.lpDraws = None
        lpPhy.Key.lpChangeTexs = None
        lpPhy = None
    
    @staticmethod
    def Phy_Calculate(lpPhy):
        result, alpha = c3_key.C3Key.Key_ProcessAlpha(lpPhy.Key, lpPhy.lpMotion.nFrame, lpPhy.lpMotion.dwFrames)
        if result:
            lpPhy.fA = alpha
        
        result, draw = c3_key.C3Key.Key_ProcessDraw(lpPhy.Key, lpPhy.lpMotion.nFrame)
        if result:
            lpPhy.bDraw = draw
        
        result, tex = c3_key.C3Key.Key_ProcessChangeTex(lpPhy.Key, lpPhy.lpMotion.nFrame)
        if not result:
            tex = -1
        
        if not lpPhy.bDraw:
            return True
        
        bone = []
        for b in range(lpPhy.lpMotion.dwBoneCount):           
            mm = c3_motion.C3Motion.Motion_GetMatrix(lpPhy.lpMotion, b)           
            bone.append(lpPhy.InitMatrix @ mm @ lpPhy.lpMotion.matrix[b])
        
        for v in range(lpPhy.dwNVecCount + lpPhy.dwAVecCount):
            mix = lpPhy.lpVB[v].pos[0]
            finalPos = Vector((0, 0, 0))
            
            for l in range(_BONE_MAX_):
                index = lpPhy.lpVB[v].index[l]
                weight = lpPhy.lpVB[v].weight[l]
                
                if weight > 0:
                    mix4d = Vector(mix).to_4d()
                    bone_transposed = bone[index]
                    vec = mix4d @ bone_transposed
                    finalPos += vec.xyz
                    break
            
            lpPhy.outputVertices[v].Position = finalPos
            lpPhy.outputVertices[v].Color = (lpPhy.fR, lpPhy.fG, lpPhy.fB, lpPhy.fA)
            lpPhy.outputVertices[v].TexCoord = lpPhy.lpVB[v].TexCoord + lpPhy.uvstep
            
            if tex > -1:
                segsize = 1.0 / lpPhy.dwTexRow
                lpPhy.outputVertices[v].TexCoord = Vector((
                    lpPhy.lpVB[v].TexCoord.x + (tex % lpPhy.dwTexRow) * segsize,
                    lpPhy.lpVB[v].TexCoord.y + (tex // lpPhy.dwTexRow) * segsize
                ))
        
        return True
    
    @staticmethod
    def Phy_NextFrame(lpPhy, nStep):
        lpPhy.lpMotion.nFrame = (lpPhy.lpMotion.nFrame + nStep) % int(lpPhy.lpMotion.dwFrames)
    
    @staticmethod
    def Phy_SetFrame(lpPhy, dwFrame):
        if lpPhy.lpMotion.dwFrames == 0:
            lpPhy.lpMotion.nFrame = 0
        else:
            lpPhy.lpMotion.nFrame = int(dwFrame % lpPhy.lpMotion.dwFrames)
    
    @staticmethod
    def Phy_Muliply(lpPhy, nBoneIndex, matrix):
        if nBoneIndex == -1:
            start = 0
            end = int(lpPhy.lpMotion.dwBoneCount)
        else:
            start = nBoneIndex
            end = start + 1
        
        for n in range(start, end):
            lpPhy.lpMotion.matrix[n] = lpPhy.lpMotion.matrix[n] @ matrix
    
    @staticmethod
    def Phy_SetColor(lpPhy, alpha, red, green, blue):
        lpPhy.fA = alpha
        lpPhy.fR = red
        lpPhy.fG = green
        lpPhy.fB = blue
    
    @staticmethod
    def Phy_ClearMatrix(lpPhy):
        for n in range(lpPhy.lpMotion.dwBoneCount):
            lpPhy.lpMotion.matrix[n] = Matrix.Identity(4)
    
    @staticmethod
    def Phy_ChangeTexture(lpPhy, nTexID, nTexID2=0):
        lpPhy.nTex = nTexID
        lpPhy.nTex2 = nTexID2