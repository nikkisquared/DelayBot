import unittest
import timeconversions as TC
import delaymessage as DM 
import DelayBot as DBot

import json

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
        
class TestDelayMessage(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass


class TestJSONMethod(unittest.TestCase):

    def setUp(self):
        self.DBot = DBot.DelayBot(DBot.zulip_username, DBot.zulip_api_key, DBot.key_word, DBot.subscribed_streams)
        self.messageObjectList = [DM.DelayMessage(i*1000, 'Eric%d'%i, i, 'Stream%d'%i, 'Topic%d'%i,'Message%d'%i) for i in range(1,10)]
        self.messageDictList = [{"timestamp":i*1000, "user":'Eric%d'%i, "uid":i, "stream":'Stream%d'%i, "topic":'Topic%d'%i,"message":'Message%d'%i} for i in range(1,10)]
        
    # def testConvertToJson(self):
        
    #     for m in self.messageObjectList:
    #         self.DBot.add_message_to_file(m)
    #     with open('messages.json') as mfile:
    #         self.assertEqual(json.load(mfile), json.dumps(self.messageDictList))
    
    def tearDown(self):
        pass

if __name__ =='__main__':
    unittest.main()