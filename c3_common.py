import struct

class ChunkHeader:
    def __init__(self):
        self.byChunkID = b''
        self.dwChunkSize = 0
    
    @property
    def ChunkID(self):
        return self.byChunkID.decode()
    
    def __str__(self):
        return f"{self.byChunkID.decode()} (Size: {self.dwChunkSize})"
    
    @staticmethod
    def read(file):
        chunk = ChunkHeader()
        chunk.byChunkID = file.read(4)
        chunk.dwChunkSize = struct.unpack('<I', file.read(4))[0]
        return chunk
