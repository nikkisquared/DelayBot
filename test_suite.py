import DelayBot as DB 
import unittest

class TestGetTimeMethod(unittest.TestCase):

    def setUp(self):
        self.DB = DB.DelayBot(DB.zulip_username, DB.zulip_api_key, DB.key_word, DB.subscribed_streams)

        
    def testBlockOverLimit(self):
        self.assertIsNone(self.DB.get_time('2d'))
        self.assertIsNone(self.DB.get_time('25h'))
        self.assertIsNone(self.DB.get_time('61m'))     
        self.assertIsNone(self.DB.get_time('61s'))
        self.assertIsNotNone(self.DB.get_time('1d'))
        self.assertIsNotNone(self.DB.get_time('24h'))
        self.assertIsNotNone(self.DB.get_time('60m'))     
        self.assertIsNotNone(self.DB.get_time('60s'))
        self.assertIsNotNone(self.DB.get_time('0d'))
        self.assertIsNotNone(self.DB.get_time('0h'))
        self.assertIsNotNone(self.DB.get_time('00m'))     
        self.assertIsNotNone(self.DB.get_time('00s'))

    def testClock24OverLimits(self):
        self.assertIsNone(self.DB.get_time('24:00'))
        self.assertIsNone(self.DB.get_time('24:01'))
        self.assertIsNotNone(self.DB.get_time('23:59'))
        self.assertIsNone(self.DB.get_time('24:00:00'))
        self.assertIsNone(self.DB.get_time('24:00:01'))
        self.assertIsNotNone(self.DB.get_time('23:00:59'))
        self.assertIsNotNone(self.DB.get_time('0:00:00'))

    def testClock12OverLimits(self):
        for meridiem in ("AM", "PM", "A.M.", "P.M.", "am", "pm", "a.m.", "p.m."):
            self.assertIsNone(self.DB.get_time('13:00%s' % meridiem))
            self.assertIsNotNone(self.DB.get_time('12:00%s' % meridiem))
            self.assertIsNone(self.DB.get_time('0:00%s' % meridiem))
            self.assertIsNotNone(self.DB.get_time('1:00%s' % meridiem))


    def tearDown(self):
        self.DB = None
        

if __name__ =='__main__':
    unittest.main()