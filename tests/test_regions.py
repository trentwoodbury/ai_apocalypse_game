import unittest
from regions import RegionManager

class TestRegions(unittest.TestCase):
    def test_presence_and_totals(self):
        rm = RegionManager(["North America","Asia"])
        self.assertEqual(rm.total_power(), 0)
        self.assertEqual(rm.total_reputation(), 0)

        rm.region_at("North America").power = 3
        rm.region_at("Asia").reputation = 4
        self.assertEqual(rm.total_power(), 3)
        self.assertEqual(rm.total_reputation(), 4)

        rm.add_presence("Asia")
        self.assertTrue(rm.has_presence("Asia"))
        self.assertFalse(rm.has_presence("North America"))
