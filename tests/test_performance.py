import math
import unittest
from prootface.model import Animator
from prootface.performance import SpeakingExample


def example():
    phones=[('pau',0,.2),('m',.2,.26),('ey',.26,.5),('b',.5,.58),
            ('iy',.58,.8),('uw',.8,1.1),('pau',1.1,1.4)]
    return SpeakingExample(dict(text='Timing test',segments=[
        dict(phone=p,start=a,end=b,word='test') for p,a,b in phones]))


class PerformanceTests(unittest.TestCase):
    def test_closure_overrides_overlapping_vowels(self):
        e=example()
        for t in (.22,.53):
            self.assertEqual(e.controls(t)['seal'],1)
        animator=Animator()
        contact=[]
        for i in range(85):
            t=i/60
            pose=animator.step(e.controls(t),t)
            if .51<t<.56:contact.append(pose['aperture'])
        self.assertTrue(contact)
        self.assertEqual(max(contact),0)

    def test_rounding_prepares_before_the_sound_and_expression_persists(self):
        e=example()
        self.assertGreater(e.controls(.77)['rounding'],.1)
        for t in (-1,0,.22,.6,.9,2):
            c=e.controls(t)
            self.assertEqual(c['corner_left'],.24)
            self.assertEqual(c['corner_right'],.20)

    def test_gestures_are_continuous_and_bounded(self):
        e=example();previous=None
        for i in range(1401):
            c=e.controls(i/1000)
            for key in ('opening','rounding','spread','seal'):
                self.assertTrue(math.isfinite(c[key]) and 0<=c[key]<=1)
                if previous:self.assertLess(abs(c[key]-previous[key]),.08)
            previous=c

    def test_invalid_intervals_are_rejected(self):
        for segments in ([],[dict(phone='m',start=.2,end=.1)],
                         [dict(phone='m',start=0,end=.4),dict(phone='b',start=.3,end=.5)]):
            with self.assertRaises(ValueError):SpeakingExample(dict(text='x',segments=segments))
