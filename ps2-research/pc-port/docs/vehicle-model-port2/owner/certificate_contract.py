"""Pure admission model for focused tests; not a game hook or authority source."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OwnerKey:
    packet:int
    instance:int
    model:int
    scene_generation:int
    reset_generation:int


@dataclass(frozen=True)
class UploadKey:
    native_vertex:int
    vertex_generation:int
    vertex_revision:int
    native_index:int
    index_generation:int
    index_revision:int


class Warmup:
    def __init__(self):
        self.key=None;self.frame=None;self.records={};self.matrix=None;self.failed=False
    def observe(self,owner,frame,source_index,upload,matrix,*,membership,source_hash_verified,
                current_native_binding,scene_verified):
        if self.key!=owner or self.frame!=frame:
            self.key=owner;self.frame=frame;self.records={};self.matrix=matrix;self.failed=False
        valid=(membership and source_hash_verified and current_native_binding and scene_verified
               and 0<=source_index<24 and all((upload.native_vertex,upload.vertex_generation,
                   upload.vertex_revision,upload.native_index,upload.index_generation,upload.index_revision))
               and self.matrix==matrix and source_index not in self.records)
        if not valid:self.failed=True;return False
        self.records[source_index]=upload
        return True
    def admit(self,owner,frame,current_uploads):
        # Source proof is from the immediately preceding completed frame;
        # every retained resource must still be live at its exact revision.
        return (not self.failed and owner==self.key and self.frame is not None
                and frame==self.frame+1 and set(self.records)==set(range(24))
                and current_uploads==self.records)
