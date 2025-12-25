import struct
from mathutils import Matrix
from . import c3_main
from . import c3_common

class C3KeyFrame:
    def __init__(self):
        self.pos = 0
        self.matrix = None

class C3Motion:
    def __init__(self):
        self.dwBoneCount = 0
        self.dwFrames = 0
        self.dwKeyFrames = 0
        self.lpKeyFrame = None
        self.matrix = None
        self.dwMorphCount = 0
        self.lpMorph = None
        self.nFrame = 0
        self.m_dwMotionNum = 0
        self.m_motion = [None] * 16
    
    @staticmethod
    def Motion_Clear(lpMotion):
        lpMotion.dwBoneCount = 0
        lpMotion.dwFrames = 0
        lpMotion.nFrame = 0
        lpMotion.dwKeyFrames = 0
        lpMotion.lpKeyFrame = None
        lpMotion.matrix = None
        lpMotion.nFrame = 0
        lpMotion.dwMorphCount = 0
        lpMotion.lpMorph = None
    
    def C3_Load(self, lpName):
        self.m_dwMotionNum = 0
        
        try:
            with open(lpName, 'rb') as file:
                version = file.read(16).decode().rstrip('\0')
                
                if version != c3_main.C3_VERSION:
                    return False
                
                add = 0
                
                while file.tell() < len(open(lpName, 'rb').read()):
                    chunk = c3_common.ChunkHeader.read(file)
                    if chunk.byChunkID == b'MOTI':
                        result, motion = C3Motion.Motion_Load(file)
                        if not result:
                            break
                        self.m_motion[self.m_dwMotionNum] = motion
                        self.m_dwMotionNum += 1
                    else:
                        file.seek(chunk.dwChunkSize, 1)
        except:
            return False
        
        return self.m_dwMotionNum > 0
    
    @staticmethod
    def Motion_Load(file):
        lpMotion = C3Motion()
        C3Motion.Motion_Clear(lpMotion)
        
        lpMotion.dwBoneCount = struct.unpack('<I', file.read(4))[0]
        lpMotion.dwFrames = struct.unpack('<I', file.read(4))[0]
        
        lpMotion.matrix = [Matrix.Identity(4) for _ in range(lpMotion.dwBoneCount)]
        
        kf = file.read(4)
        if kf == b'KKEY':
            lpMotion.dwKeyFrames = struct.unpack('<I', file.read(4))[0]
            lpMotion.lpKeyFrame = []
            
            for kk in range(lpMotion.dwKeyFrames):
                keyframe = C3KeyFrame()
                keyframe.pos = struct.unpack('<I', file.read(4))[0]
                keyframe.matrix = []
                
                for bb in range(lpMotion.dwBoneCount):
                    keyframe.matrix.append(C3Motion.ReadMatrix(file))
                
                lpMotion.lpKeyFrame.append(keyframe)
        
        elif kf == b'ZKEY':
            lpMotion.dwKeyFrames = struct.unpack('<I', file.read(4))[0]
            lpMotion.lpKeyFrame = []
            
            for kk in range(lpMotion.dwKeyFrames):
                keyframe = C3KeyFrame()
                wPos = struct.unpack('<H', file.read(2))[0]
                keyframe.pos = wPos
                keyframe.matrix = []
                
                for bb in range(lpMotion.dwBoneCount):
                    qx = struct.unpack('<f', file.read(4))[0]
                    qy = struct.unpack('<f', file.read(4))[0]
                    qz = struct.unpack('<f', file.read(4))[0]
                    qw = struct.unpack('<f', file.read(4))[0]
                    
                    x = struct.unpack('<f', file.read(4))[0]
                    y = struct.unpack('<f', file.read(4))[0]
                    z = struct.unpack('<f', file.read(4))[0]
                    
                    mat = C3Motion.create_from_quaternion(qx, qy, qz, qw)                   
                    mat[3][0] = x
                    mat[3][1] = y
                    mat[3][2] = z
                    mat[3][3] = 1.0  

                    keyframe.matrix.append(mat)
                
                lpMotion.lpKeyFrame.append(keyframe)
        
        elif kf == b'XKEY':
            lpMotion.dwKeyFrames = struct.unpack('<I', file.read(4))[0]
            lpMotion.lpKeyFrame = []
            
            for kk in range(lpMotion.dwKeyFrames):
                keyframe = C3KeyFrame()
                wPos = struct.unpack('<H', file.read(2))[0]
                keyframe.pos = wPos
                keyframe.matrix = []
                
                for bb in range(lpMotion.dwBoneCount):
                    _11 = struct.unpack('<f', file.read(4))[0]
                    _12 = struct.unpack('<f', file.read(4))[0]
                    _13 = struct.unpack('<f', file.read(4))[0]
                    _21 = struct.unpack('<f', file.read(4))[0]
                    _22 = struct.unpack('<f', file.read(4))[0]
                    _23 = struct.unpack('<f', file.read(4))[0]
                    _31 = struct.unpack('<f', file.read(4))[0]
                    _32 = struct.unpack('<f', file.read(4))[0]
                    _33 = struct.unpack('<f', file.read(4))[0]
                    _41 = struct.unpack('<f', file.read(4))[0]
                    _42 = struct.unpack('<f', file.read(4))[0]
                    _43 = struct.unpack('<f', file.read(4))[0]
                    
                    mat = Matrix((
                        (_11, _12, _13, 0.0),
                        (_21, _22, _23, 0.0),
                        (_31, _32, _33, 0.0),
                        (_41, _42, _43, 1.0)
                    ))
                    
                    keyframe.matrix.append(mat)
                
                lpMotion.lpKeyFrame.append(keyframe)
        
        else:
            file.seek(-4, 1)
            
            lpMotion.dwKeyFrames = lpMotion.dwFrames
            lpMotion.lpKeyFrame = []
            
            for kk in range(lpMotion.dwFrames):
                keyframe = C3KeyFrame()
                keyframe.pos = kk
                keyframe.matrix = []
                lpMotion.lpKeyFrame.append(keyframe)
            
            for bb in range(lpMotion.dwBoneCount):
                for kk in range(lpMotion.dwFrames):
                    lpMotion.lpKeyFrame[kk].matrix.append(C3Motion.ReadMatrix(file))
        
        lpMotion.dwMorphCount = struct.unpack('<I', file.read(4))[0]
        lpMotion.lpMorph = []
        for i in range(lpMotion.dwMorphCount * lpMotion.dwFrames):
            lpMotion.lpMorph.append(struct.unpack('<f', file.read(4))[0])
        
        return True, lpMotion

    @staticmethod
    def create_from_quaternion(qx, qy, qz, qw):
        # Precompute products (same as C# code)
        num  = qx * qx
        num2 = qy * qy
        num3 = qz * qz
        num4 = qx * qy
        num5 = qz * qw
        num6 = qz * qx
        num7 = qy * qw
        num8 = qy * qz
        num9 = qx * qw

        # Build 4x4 matrix (row-major like C#)
        mat = Matrix((
            (1.0 - 2.0 * (num2 + num3),  2.0 * (num4 + num5),       2.0 * (num6 - num7),       0.0),
            (2.0 * (num4 - num5),        1.0 - 2.0 * (num3 + num),  2.0 * (num8 + num9),       0.0),
            (2.0 * (num6 + num7),        2.0 * (num8 - num9),       1.0 - 2.0 * (num2 + num),  0.0),
            (0.0,                        0.0,                       0.0,                       1.0)
        ))

        return mat

    
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
    def Motion_Unload(lpMotion):
        if lpMotion.lpKeyFrame is not None:
            for kk in range(lpMotion.dwKeyFrames):
                lpMotion.lpKeyFrame[kk].matrix = None
        lpMotion.lpKeyFrame = None
        lpMotion.matrix = None
        lpMotion.lpMorph = None
        lpMotion = None
    
    @staticmethod
    def Motion_GetMatrix(lpMotion, dwBone):
        lpMatrix = Matrix.Identity(4)
        
        sindex = -1
        eindex = -1
        
        for n in range(int(lpMotion.dwKeyFrames)):
            if lpMotion.lpKeyFrame[n].pos <= lpMotion.nFrame:
                if sindex == -1 or n > sindex:
                    sindex = n
            if lpMotion.lpKeyFrame[n].pos > lpMotion.nFrame:
                if eindex == -1 or n < eindex:
                    eindex = n
        
        if sindex == -1 and eindex > -1:
            lpMatrix = lpMotion.lpKeyFrame[eindex].matrix[dwBone].copy()
        elif sindex > -1 and eindex == -1:
            lpMatrix = lpMotion.lpKeyFrame[sindex].matrix[dwBone].copy()
        elif sindex > -1 and eindex > -1:
            t = float(lpMotion.nFrame - lpMotion.lpKeyFrame[sindex].pos) / \
                float(lpMotion.lpKeyFrame[eindex].pos - lpMotion.lpKeyFrame[sindex].pos)
            
            mat_s = lpMotion.lpKeyFrame[sindex].matrix[dwBone]
            mat_e = lpMotion.lpKeyFrame[eindex].matrix[dwBone]
            
            lpMatrix = C3Motion.lerp_matrix(mat_s, mat_e, t)
        
        return lpMatrix

    @staticmethod
    def lerp_matrix(mat_s, mat_e, t):
        return Matrix([
        [mat_s[i][j] + (mat_e[i][j] - mat_s[i][j]) * t for j in range(4)]
        for i in range(4)
        ])

