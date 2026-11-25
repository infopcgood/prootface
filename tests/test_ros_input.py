import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace as NS
import unittest
import urllib.request

from prootface.openseeface import FEATURES, HEADER, decode_packet
from prootface.ros_input import measurement_from_ros, ros_feature_name
from prootface.server import Application, start_http
from test_core import packet


def ros_message(data):
    h=HEADER.unpack_from(data);offset=HEADER.size
    confidence=struct.unpack_from('<68f',data,offset)
    points=struct.unpack_from('<136f',data,offset+68*4)
    features=struct.unpack_from('<14f',data,len(data)-56)
    return NS(time=h[0],id=h[1],resolution=h[2:4],right_eye_open=h[4],left_eye_open=h[5],
              got_3d_points=bool(h[6]),confidence=confidence,
              points=[NS(x=points[i],y=points[i+1],z=0.) for i in range(0,136,2)],
              **{ros_feature_name(k):v for k,v in zip(FEATURES,features)})


class ROSInputTests(unittest.TestCase):
    def test_wire_and_ros_paths_produce_identical_measurements_and_contact(self):
        for gap in (0,2,30):
            data=packet(face_id=3,gap=gap)
            a=decode_packet(data,5)[0];b=measurement_from_ros(ros_message(data),5)
            self.assertEqual(a,b)
            apps=[Application(Path('/nonexistent/profile')) for _ in range(2)]
            for app in apps:app.face_id=3;app.mode='live'
            apps[0].receive(data,5);apps[1].ingest(b)
            for app in apps:app.tick(5)
            self.assertEqual(apps[0].snapshot['pose'],apps[1].snapshot['pose'])

    def test_raw_eye_openness_and_local_clock_are_used(self):
        message=ros_message(packet());message.eye_left=-1;message.eye_right=-1
        m=measurement_from_ros(message,40)
        self.assertAlmostEqual(m.eye_left,.9,places=6)
        self.assertAlmostEqual(m.eye_right,.8,places=6)
        self.assertEqual(m.received_at,40);self.assertNotEqual(m.sender_time,40)
        app=Application(Path('/nonexistent/profile'));app.mode='live';app.ingest(m);app.tick(40.3)
        self.assertFalse(app.snapshot['tracking'])

    def test_invalid_ros_input_does_not_become_a_valid_measurement(self):
        for field,value in [('mouth_open',float('nan')),('resolution',[0,480]),('points',[])]:
            message=ros_message(packet());setattr(message,field,value)
            with self.assertRaises(ValueError):measurement_from_ros(message,1)
        message=ros_message(packet());message.confidence=list(message.confidence);message.confidence[60]=.1
        self.assertFalse(measurement_from_ros(message,1).valid)

    def test_same_calibration_http_server_works_with_decoded_input(self):
        with tempfile.TemporaryDirectory() as root:
            app=Application(Path(root)/'profile.json');app.tick(0)
            server,thread=start_http(app,'127.0.0.1',0,Path(root)/'character.json')
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                request=urllib.request.Request(base+'/api/calibration/start',
                    json.dumps({'stage':'neutral'}).encode(),{'Content-Type':'application/json'})
                with urllib.request.urlopen(request) as response:self.assertEqual(response.status,200)
                app.ingest(measurement_from_ros(ros_message(packet()),1));app.tick(1)
                with urllib.request.urlopen(base+'/api/state') as response:state=json.load(response)
                self.assertEqual(state['calibration']['counts']['neutral'],1)
                self.assertEqual(state['mode'],'live')
            finally:
                app.stop.set();server.shutdown();server.server_close();thread.join(2)
