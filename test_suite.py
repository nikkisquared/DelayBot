#!usr/bin/python

from __future__ import unicode_literals

import unittest
import timeconversions as TC
import delaymessage as DM

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

        # testing over limits (d = 2, h = 25, m/s = 61)
        badTimes = [
            "2d", "25h", "61m", "61s",
            "2d25h61m61s",
            # all 0 values means no time delay, which is invalid
            "0d", "0h", "00m", "00s",
            "0d0h0m0s",
            ]
        for t in badTimes:
            with self.assertRaises(ValueError):
                TC.get_time(t)

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


if __name__ == "__main__":
    unittest.main()
