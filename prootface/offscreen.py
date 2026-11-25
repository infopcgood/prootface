"""Headless EGL/OpenGL ES renderer for the same schema-2 mesh as the viewer.

No browser or Blender is used. NumPy blends sparse authored targets; GLES draws
emission and occlusion with depth, then reads a top-left, BGR two-view atlas.
Create, render and close on one thread. EGL may select software Mesa on hosts
without a GPU; callers must inspect info before making performance claims.
"""
import ctypes as C
from ctypes.util import find_library
import json
import math
from pathlib import Path
import threading
from types import SimpleNamespace

import numpy as np
from PIL import Image

from .rig import FRONT_TARGETS, front_motion_weights

I=C.c_int; U=C.c_uint; F=C.c_float; P=C.c_void_p

VERTEX = b'''
attribute vec3 position; attribute vec2 texcoord;
uniform float zoom; uniform vec2 offset; uniform float mirror; uniform float depthSign;
varying vec2 uv;
void main(){
 vec2 clip=vec2(position.x/1.88,(position.y+.14)/1.16)*zoom+offset;
 gl_Position=vec4(clip.x*mirror,clip.y,-position.z*depthSign*.25,1.);
 uv=texcoord;
}'''
FRAGMENT = b'''
precision mediump float;
uniform bool textured; uniform sampler2D emissionMap;
varying vec2 uv;
void main(){gl_FragColor=vec4(textured?texture2D(emissionMap,uv).rgb:vec3(0.),1.);}
'''


class CompiledMesh:
    def __init__(self, character):
        if character.get('schema')!=2:
            raise ValueError('Live renderer requires a privately compiled schema-2 character')
        self.base=np.asarray(character['positions'],dtype=np.float32).reshape(-1,3)
        self.uv=np.asarray(character['uvs'],dtype=np.float32).reshape(-1,2)
        if len(self.uv)!=len(self.base) or not np.isfinite(self.base).all() or not np.isfinite(self.uv).all():
            raise ValueError('Invalid character vertex/UV data')
        self.front=np.asarray(character.get('front_weights',front_motion_weights(character)),dtype=np.float32)
        if self.front.shape!=(len(self.base),) or not np.isfinite(self.front).all():
            raise ValueError('Invalid anterior guide')
        self.targets={}
        for name,t in character['targets'].items():
            indices=np.asarray(t['indices'],dtype=np.intp)
            deltas=np.asarray(t['deltas'],dtype=np.float32).reshape(-1,3)
            if (len(indices)!=len(deltas) or len(set(indices.tolist()))!=len(indices)
                    or (len(indices) and (indices.min()<0 or indices.max()>=len(self.base)))
                    or not np.isfinite(deltas).all()):
                raise ValueError('Invalid sparse target')
            self.targets[name]=(indices,deltas)
        indices=[];self.parts=[]
        for part in character['parts']:
            start=len(indices);values=part['indices']
            if len(values)%3 or any(int(v)!=v or v<0 or v>=len(self.base) for v in values):
                raise ValueError('Invalid triangle indices')
            indices.extend(values);self.parts.append((start,len(values),bool(part['textured'])))
        self.indices=np.asarray(indices,dtype=np.intp)
        self.draw_uv=np.ascontiguousarray(self.uv[self.indices])
        self.zoom=float(character['view']['zoom']);self.offset=tuple(character['view']['offset'])
        self.left_sign=float(character.get('anatomical_left_sign',1))
        if (not all(math.isfinite(v) for v in (self.zoom,*self.offset,self.left_sign))
                or len(self.offset)!=2 or self.left_sign not in (-1,1) or self.zoom<=0):
            raise ValueError('Invalid character view')

    def vertices(self, pose):
        output=self.base.copy()
        front=float(pose.get('front_motion_scale',1))
        if not math.isfinite(front):raise ValueError('Non-finite front motion')
        front=max(0,min(1,front))
        for name,(indices,deltas) in self.targets.items():
            weight=float(pose.get('blend_'+name,0))
            if not math.isfinite(weight):raise ValueError('Non-finite target weight')
            weight=max(0,min(1,weight))
            if weight<1e-7:continue
            gain=1-(1-front)*self.front[indices] if name in FRONT_TARGETS else np.ones(len(indices),dtype=np.float32)
            output[indices]+=weight*deltas*gain[:,None]
        return output


class OffscreenRenderer:
    _display_lock=threading.Lock()
    _display_refs={}

    def __init__(self, character_path, side_width=256, side_height=144, platform='auto'):
        if (isinstance(side_width,bool) or isinstance(side_height,bool) or
                int(side_width)!=side_width or int(side_height)!=side_height or
                not 1<=side_width<=4096 or not 1<=side_height<=4096):
            raise ValueError('Side dimensions must be integers in [1,4096]')
        if platform not in ('auto','surfaceless','default'):
            raise ValueError('EGL platform must be auto, surfaceless or default')
        self.owner=threading.get_ident();self.closed=False
        self.display=None;self.surface=None;self.context=None;self.gl=None
        self.buffers=[];self.texture=0;self.program=0
        self.width=int(side_width);self.height=int(side_height)
        path=Path(character_path)
        self.mesh=CompiledMesh(json.loads(path.read_text()))
        with Image.open(path.with_suffix('.png')) as texture:
            self.pixels=np.ascontiguousarray(np.array(texture.convert('RGBA'))[::-1])
        library=find_library('EGL')
        if not library:raise RuntimeError('EGL is unavailable; install Mesa EGL and a suitable GLES driver')
        self.egl=C.CDLL(library)
        self.egl.eglGetProcAddress.argtypes=[C.c_char_p];self.egl.eglGetProcAddress.restype=P
        try:
            self._initialize(platform)
        except BaseException:
            self.close()
            raise

    def _egl(self,name,result,args):
        function=getattr(self.egl,name,None)
        if function is None:
            address=self.egl.eglGetProcAddress(name.encode())
            if not address:raise RuntimeError(f'EGL entry point unavailable: {name}')
            function=C.CFUNCTYPE(result,*args)(address)
        function.restype=result;function.argtypes=args
        return function

    def _require(self,result,operation):
        if not result:
            error=self._egl('eglGetError',I,[])()
            raise RuntimeError(f'{operation} failed (EGL 0x{error:04x})')
        return result

    def _initialize(self,platform):
        init=self._egl('eglInitialize',U,[P,C.POINTER(I),C.POINTER(I)])
        candidates=[]
        if platform!='default':
            try:
                get=self._egl('eglGetPlatformDisplay',P,[U,P,P])
            except RuntimeError:
                get=self._egl('eglGetPlatformDisplayEXT',P,[U,P,P])
            candidates.append(get(0x31DD,None,None))
        if platform!='surfaceless':
            candidates.append(self._egl('eglGetDisplay',P,[P])(None))
        with self._display_lock:
            for display in candidates:
                if not display:continue
                if display in self._display_refs or init(display,C.byref(I()),C.byref(I())):
                    self.display=display
                    self._display_refs[display]=self._display_refs.get(display,0)+1
                    break
        if not self.display:raise RuntimeError('Cannot initialize EGL; check the Mesa driver and render-device access')
        self._require(self._egl('eglBindAPI',U,[U])(0x30A0),'eglBindAPI')
        attributes=(I*15)(0x3033,1,0x3040,4,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3025,16,0x3038)
        config=P();count=I()
        self._require(self._egl('eglChooseConfig',U,[P,C.POINTER(I),C.POINTER(P),I,C.POINTER(I)])(
            self.display,attributes,C.byref(config),1,C.byref(count)) and count.value,'eglChooseConfig')
        self.surface=self._require(self._egl('eglCreatePbufferSurface',P,[P,P,C.POINTER(I)])(
            self.display,config,(I*5)(0x3057,self.width*2,0x3056,self.height,0x3038)),'eglCreatePbufferSurface')
        self.context=self._require(self._egl('eglCreateContext',P,[P,P,P,C.POINTER(I)])(
            self.display,config,None,(I*3)(0x3098,2,0x3038)),'eglCreateContext')
        self._current()
        specs={
            'GetString':(C.c_char_p,[U]),'GetError':(U,[]),
            'CreateShader':(U,[U]),'ShaderSource':(None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),
            'CompileShader':(None,[U]),'GetShaderiv':(None,[U,U,C.POINTER(I)]),
            'GetShaderInfoLog':(None,[U,I,C.POINTER(I),P]),'DeleteShader':(None,[U]),
            'CreateProgram':(U,[]),'AttachShader':(None,[U,U]),'LinkProgram':(None,[U]),
            'GetProgramiv':(None,[U,U,C.POINTER(I)]),'GetProgramInfoLog':(None,[U,I,C.POINTER(I),P]),
            'UseProgram':(None,[U]),'DeleteProgram':(None,[U]),
            'GetAttribLocation':(I,[U,C.c_char_p]),'GetUniformLocation':(I,[U,C.c_char_p]),
            'Uniform1f':(None,[I,F]),'Uniform2f':(None,[I,F,F]),'Uniform1i':(None,[I,I]),
            'GenBuffers':(None,[I,C.POINTER(U)]),'BindBuffer':(None,[U,U]),
            'BufferData':(None,[U,C.c_ssize_t,P,U]),'DeleteBuffers':(None,[I,C.POINTER(U)]),
            'EnableVertexAttribArray':(None,[U]),'VertexAttribPointer':(None,[U,I,U,C.c_ubyte,I,P]),
            'GenTextures':(None,[I,C.POINTER(U)]),'BindTexture':(None,[U,U]),
            'TexParameteri':(None,[U,U,I]),'PixelStorei':(None,[U,I]),
            'TexImage2D':(None,[U,I,I,I,I,I,U,U,P]),'DeleteTextures':(None,[I,C.POINTER(U)]),
            'Enable':(None,[U]),'Viewport':(None,[I,I,I,I]),'ClearColor':(None,[F,F,F,F]),
            'Clear':(None,[U]),'DrawArrays':(None,[U,I,I]),'ReadPixels':(None,[I,I,I,I,U,U,P]),
        }
        functions={}
        for name,(result,args) in specs.items():
            address=self.egl.eglGetProcAddress(('gl'+name).encode())
            if not address:raise RuntimeError('Missing GLES function: '+name)
            functions[name]=C.CFUNCTYPE(result,*args)(address)
        self.gl=SimpleNamespace(**functions);g=self.gl
        self.info={key:g.GetString(value).decode(errors='replace') for key,value in
                   [('vendor',0x1F00),('renderer',0x1F01),('version',0x1F02)]}
        shaders=[]
        try:
            for kind,source in [(0x8B31,VERTEX),(0x8B30,FRAGMENT)]:
                shader=g.CreateShader(kind);shaders.append(shader);text=C.c_char_p(source)
                g.ShaderSource(shader,1,C.byref(text),None);g.CompileShader(shader)
                status=I();g.GetShaderiv(shader,0x8B81,C.byref(status))
                if not status.value:
                    log=C.create_string_buffer(8192);g.GetShaderInfoLog(shader,8192,None,log)
                    raise RuntimeError('GLES shader: '+log.value.decode(errors='replace'))
            self.program=g.CreateProgram()
            for shader in shaders:g.AttachShader(self.program,shader)
            g.LinkProgram(self.program);status=I();g.GetProgramiv(self.program,0x8B82,C.byref(status))
            if not status.value:
                log=C.create_string_buffer(8192);g.GetProgramInfoLog(self.program,8192,None,log)
                raise RuntimeError('GLES link: '+log.value.decode(errors='replace'))
        finally:
            for shader in shaders:g.DeleteShader(shader)
        g.UseProgram(self.program)
        self.uniforms={name:g.GetUniformLocation(self.program,name.encode()) for name in
                       ('zoom','offset','mirror','depthSign','textured','emissionMap')}
        for name,size,data in [('position',3,None),('texcoord',2,self.mesh.draw_uv)]:
            buffer=U();g.GenBuffers(1,C.byref(buffer));self.buffers.append(buffer.value)
            g.BindBuffer(0x8892,buffer.value)
            if data is not None:g.BufferData(0x8892,data.nbytes,data.ctypes.data_as(P),0x88E4)
            location=g.GetAttribLocation(self.program,name.encode())
            g.EnableVertexAttribArray(location);g.VertexAttribPointer(location,size,0x1406,0,0,None)
        texture=U();g.GenTextures(1,C.byref(texture));self.texture=texture.value;g.BindTexture(0x0DE1,self.texture)
        for key,value in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)]:
            g.TexParameteri(0x0DE1,key,value)
        g.PixelStorei(0x0CF5,1)
        g.TexImage2D(0x0DE1,0,0x1908,self.pixels.shape[1],self.pixels.shape[0],0,0x1908,0x1401,self.pixels.ctypes.data_as(P))
        g.Uniform1i(self.uniforms['emissionMap'],0);g.Enable(0x0B71)
        self.readback=np.empty((self.height,self.width*2,4),dtype=np.uint8)

    def _current(self):
        if threading.get_ident()!=self.owner:raise RuntimeError('EGL renderer used from another thread')
        self._require(self._egl('eglMakeCurrent',U,[P,P,P,P])(
            self.display,self.surface,self.surface,self.context),'eglMakeCurrent')

    def render_atlas(self,pose):
        if self.closed:raise RuntimeError('Renderer is closed')
        self._current();g=self.gl;g.UseProgram(self.program)
        vertices=np.ascontiguousarray(self.mesh.vertices(pose)[self.mesh.indices])
        g.BindBuffer(0x8892,self.buffers[0]);g.BufferData(0x8892,vertices.nbytes,vertices.ctypes.data_as(P),0x88E8)
        g.ClearColor(0,0,0,1);g.Clear(0x4000|0x0100)
        g.Uniform1f(self.uniforms['zoom'],self.mesh.zoom)
        g.Uniform2f(self.uniforms['offset'],*self.mesh.offset)
        for column,sign,mirror in [(0,self.mesh.left_sign,-1),(1,-self.mesh.left_sign,1)]:
            g.Viewport(column*self.width,0,self.width,self.height)
            g.Uniform1f(self.uniforms['depthSign'],sign);g.Uniform1f(self.uniforms['mirror'],mirror)
            for first,count,textured in self.mesh.parts:
                g.Uniform1i(self.uniforms['textured'],int(textured));g.DrawArrays(0x0004,first,count)
        g.ReadPixels(0,0,self.width*2,self.height,0x1908,0x1401,self.readback.ctypes.data_as(P))
        error=g.GetError()
        if error:raise RuntimeError(f'GLES frame failed (0x{error:04x})')
        return self.readback[::-1,:,2::-1].copy()

    def close(self):
        if self.closed:return
        if threading.get_ident()!=self.owner:raise RuntimeError('Close renderer on its owning thread')
        if self.context and self.surface:
            self._current()
            if self.gl:
                if self.buffers:self.gl.DeleteBuffers(len(self.buffers),(U*len(self.buffers))(*self.buffers))
                if self.texture:self.gl.DeleteTextures(1,C.byref(U(self.texture)))
                if self.program:self.gl.DeleteProgram(self.program)
        if self.display:
            self._egl('eglMakeCurrent',U,[P,P,P,P])(self.display,None,None,None)
            if self.context:self._egl('eglDestroyContext',U,[P,P])(self.display,self.context)
            if self.surface:self._egl('eglDestroySurface',U,[P,P])(self.display,self.surface)
            with self._display_lock:
                self._display_refs[self.display]-=1
                if not self._display_refs[self.display]:
                    self._egl('eglTerminate',U,[P])(self.display);del self._display_refs[self.display]
        self.closed=True

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
