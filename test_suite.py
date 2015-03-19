import unittest
import timeconversions as TC
import delaymessage as DM 
import DelayBot as DBot

class TestGetTimeMethod(unittest.TestCase):

    def setUp(self):
        pass
        
    def testBlockLimits(self):
        self.assertIsNone(TC.get_time('0d'))
        self.assertIsNotNone(TC.get_time('1d'))
        self.assertIsNone(TC.get_time('2d'))

        self.assertIsNone(TC.get_time('0h'))
        self.assertIsNotNone(TC.get_time('24h'))
        self.assertIsNone(TC.get_time('25h'))

        self.assertIsNone(TC.get_time('00m'))
        self.assertIsNotNone(TC.get_time('60m'))
        self.assertIsNone(TC.get_time('61m'))

        self.assertIsNone(TC.get_time('00s'))
        self.assertIsNotNone(TC.get_time('60s'))
        self.assertIsNone(TC.get_time('61s'))

        self.assertIsNone(TC.get_time('0d0h0m0s'))
        self.assertIsNotNone(TC.get_time('0d24h60m60s'))
        self.assertIsNotNone(TC.get_time('1d0h60m60s'))
        self.assertIsNotNone(TC.get_time('1d24h0m60s'))
        self.assertIsNotNone(TC.get_time('1d24h60m0s'))
        self.assertIsNotNone(TC.get_time('1d24h60m60s'))


    def testClock24Limits(self):
        self.assertIsNone(TC.get_time('24:00'))
        self.assertIsNone(TC.get_time('24:01'))
        self.assertIsNone(TC.get_time('24:00:00'))
        self.assertIsNone(TC.get_time('24:00:01'))
        self.assertIsNone(TC.get_time('24:01:01'))

        self.assertIsNone(TC.get_time('0'))
        self.assertIsNotNone(TC.get_time('0:00'))
        self.assertIsNotNone(TC.get_time('0:00:00'))
        self.assertIsNone(TC.get_time('00:60'))
        self.assertIsNone(TC.get_time('00:00:60'))

        self.assertIsNotNone(TC.get_time('23:59'))
        self.assertIsNotNone(TC.get_time('23:00:59'))
        self.assertIsNotNone(TC.get_time('23:59:59'))


    def testClock12Limits(self):
        for meridiem in ("AM", "PM", "A.M.", "P.M."):
            self.assertIsNone(TC.get_time('13:00%s' % meridiem))
            self.assertIsNone(TC.get_time('13:01%s' % meridiem))
            self.assertIsNone(TC.get_time('13:00:01%s' % meridiem))
            self.assertIsNotNone(TC.get_time('1:00%s' % meridiem))
            self.assertIsNone(TC.get_time('1:60%s' % meridiem))
            self.assertIsNone(TC.get_time('1:00:60%s' % meridiem))

            self.assertIsNone(TC.get_time('0:00%s' % meridiem))
            self.assertIsNotNone(TC.get_time('12:00%s' % meridiem))
            self.assertIsNotNone(TC.get_time('12:59%s' % meridiem))
            self.assertIsNotNone(TC.get_time('12:00:59%s' % meridiem))
            self.assertIsNotNone(TC.get_time('12:59:59%s' % meridiem))


    def tearDown(self):
        pass
        

class TestJSONMethod(unittest.TestCase):

    def setup(self):
        pass


    def testConvertToJson(self):
        pass

    def tearDown(self):
        pass

if __name__ =='__main__':
    unittest.main()