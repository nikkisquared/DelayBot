import unittest
import timeconversions as TC
import delaymessage as DM 
import DelayBot as DBot

import json

class TestGetTimeMethod(unittest.TestCase):
    
    def setUp(self):
        self.meridiems = ("AM", "PM", "A.M.", "P.M.", "am", "pm", "a.m.", "p.m.")
        self.badMeridiems = ("AA", "AAM", "PP", "PMM", "MM", "A..M..", "PM..", ".A.M", "P.M",
                            "aa", "aam", "pp", "pmm", "mm", "a..m..", "pm..", ".a.m", "p.m")

    def testBlock(self):
        # testing exact limits (d = 1, h = 24, m/s = 60)
        self.assertIsNotNone(TC.get_time("1d"))
        self.assertIsNotNone(TC.get_time("24h"))
        self.assertIsNotNone(TC.get_time("60m"))
        self.assertIsNotNone(TC.get_time("60s"))
        # going definitively beyond 11:59PM the next day is valid
        self.assertIsNotNone(TC.get_time("1d24h60m60s"))

        with self.assertRaises(ValueError):
            # testing over limits (d = 2, h = 25, m/s = 61)
            TC.get_time("2d")
            TC.get_time("25h")
            TC.get_time("61m")
            TC.get_time("61s")
            TC.get_time("2d25h61m61s")

            # all 0 values means no time delay, which is invalid
            TC.get_time("0d")
            TC.get_time("0h")
            TC.get_time("00m")
            TC.get_time("00s")
            TC.get_time("0d0h0m0s")

        # a single 0 value is acceptable
        self.assertIsNotNone(TC.get_time("0d24h60m60s"))
        self.assertIsNotNone(TC.get_time("1d0h60m60s"))
        self.assertIsNotNone(TC.get_time("1d24h0m60s"))
        self.assertIsNotNone(TC.get_time("1d24h60m0s"))


    def testClock24hr(self):
        with self.assertRaises(ValueError):
            TC.get_time("24:00")
            TC.get_time("24:01")
            TC.get_time("24:00:00")
            TC.get_time("24:00:01")
            TC.get_time("24:01:01")
            TC.get_time("24:01:00")

        self.assertRaises(ValueError, TC.get_time, "0")
        self.assertIsNotNone(TC.get_time("0:00"))
        self.assertIsNotNone(TC.get_time("0:00:00"))
        self.assertRaises(ValueError, TC.get_time, "00:60")
        self.assertRaises(ValueError, TC.get_time, "00:00:60")

        self.assertIsNotNone(TC.get_time("23:59"))
        self.assertIsNotNone(TC.get_time("23:00:59"))
        self.assertIsNotNone(TC.get_time("23:59:59"))


    def testClock12hr(self):
        for meridiem in self.meridiems:

            with self.assertRaises(ValueError):
                # testing over limits (h = 13, m/s = 60)
                TC.get_time("13:00%s" % meridiem)
                TC.get_time("1:60%s" % meridiem)
                TC.get_time("1:00:60%s" % meridiem)
                TC.get_time()
                self.assertRaises(ValueError, TC.get_time, )

                # cannot give 0 as an hour
                self.assertRaises(ValueError, TC.get_time, "0:00%s" % meridiem)

            # testing equal to limits (h = 12, m/s = 59)
            self.assertIsNotNone(TC.get_time("12:00%s" % meridiem))
            self.assertIsNotNone(TC.get_time("12:59%s" % meridiem))
            self.assertIsNotNone(TC.get_time("12:00:59%s" % meridiem))
            self.assertIsNotNone(TC.get_time("12:59:59%s" % meridiem))


    def testSingleHour(self):
        for meridiem in self.meridiems:
            # testing that single hour clock formats work
            self.assertIsNotNone(TC.get_time("1%s" % meridiem))
            # cannot give 0 as an hour
            self.assertRaises(ValueError, TC.get_time,  "0%s" % meridiem)
            # testing over limit (h = 13)
            self.assertRaises(ValueError, TC.get_time, "13%s" % meridiem)
            # testing equal to limits (h = 12)
            self.assertIsNotNone(TC.get_time("12%s" % meridiem))


    def testBadMeridiems(self):
        for meridiem in self.badMeridiems:
            with self.assertRaises(ValueError):
                TC.get_time("12%s" % meridiem)
                TC.get_time("12:00%s" % meridiem)
                TC.get_time("12:00:00%s" % meridiem)

        
class TestDelayMessage(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass


class TestJSONMethod(unittest.TestCase):

    def setUp(self):
        self.DBot = DBot.DelayBot(DBot.zulip_username, DBot.zulip_api_key, DBot.key_word, DBot.subscribed_streams)
        self.messageObjectList = [DM.DelayMessage(i*1000, "Eric%d"%i, i, "Stream%d"%i, "Topic%d"%i,"Message%d"%i) for i in range(1,10)]
        self.messageDictList = [{"timestamp":i*1000, "user":"Eric%d"%i, "uid":i, "stream":"Stream%d"%i, "topic":"Topic%d"%i,"message":"Message%d"%i} for i in range(1,10)]
        
    # def testConvertToJson(self):
        
    #     for m in self.messageObjectList:
    #         self.DBot.add_message_to_file(m)
    #     with open("messages.json") as mfile:
    #         self.assertEqual(json.load(mfile), json.dumps(self.messageDictList))
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()