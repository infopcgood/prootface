"""Optional review-audio tool using locally installed CMU Flite shared libraries.

This calls Flite's public C API; it does not copy synthesis code or avatar keys.
python tools/synthesize_example.py local/sentence
"""
import argparse
import ctypes as C
import json
from pathlib import Path


def synthesize(text, destination):
    destination.mkdir(parents=True, exist_ok=True)
    flite = C.CDLL('libflite.so.1', mode=C.RTLD_GLOBAL)
    voice_library = C.CDLL('libflite_cmu_us_slt.so.1', mode=C.RTLD_GLOBAL)
    def function(library, name, result, arguments):
        fn = getattr(library, name)
        fn.restype, fn.argtypes = result, arguments
        return fn
    ptr, string = C.c_void_p, C.c_char_p
    function(flite, 'flite_init', C.c_int, [])()
    voice = function(voice_library, 'register_cmu_us_slt', ptr, [string])(None)
    utterance = function(flite, 'flite_synth_text', ptr, [string, ptr])(text.encode(), voice)
    if not utterance:
        raise RuntimeError('Flite could not synthesize the example')
    try:
        relation = function(flite, 'utt_relation', ptr, [ptr, string])(utterance, b'Segment')
        item = function(flite, 'relation_head', ptr, [ptr])(relation)
        next_item = function(flite, 'item_next', ptr, [ptr])
        feature_string = function(flite, 'item_feat_string', string, [ptr, string])
        feature_float = function(flite, 'item_feat_float', C.c_float, [ptr, string])
        path_string = function(flite, 'ffeature_string', string, [ptr, string])
        segments, start = [], 0.0
        while item:
            end = float(feature_float(item, b'end'))
            segments.append(dict(phone=feature_string(item,b'name').decode(),
                                 word=path_string(item,b'R:SylStructure.parent.parent.name').decode(),
                                 start=start, end=end))
            start, item = end, next_item(item)
        wave = function(flite, 'utt_wave', ptr, [ptr])(utterance)
        result = function(flite, 'cst_wave_save_riff', C.c_int, [ptr, string])(
            wave, str((destination/'voice.wav').resolve()).encode())
        if result:
            raise RuntimeError('Could not save synthesized speech')
        data = dict(text=text, voice='CMU Flite SLT', segments=segments)
        (destination/'phonemes.json').write_text(json.dumps(data, indent=2)+'\n')
        print(f'Synthesized {len(segments)} timing segments / {start:.3f} seconds')
    finally:
        function(flite, 'delete_utterance', None, [ptr])(utterance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--text', default='Maybe we should move a little closer.')
    args = parser.parse_args()
    synthesize(args.text, args.destination)
