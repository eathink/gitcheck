import unittest

from gitcheck.human import human_size, parse_size


class HumanTests(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(human_size(0), "0 B")
        self.assertEqual(human_size(1023), "1023 B")
        self.assertEqual(human_size(1024), "1.0 KiB")
        self.assertEqual(human_size(1536), "1.5 KiB")

    def test_parse_size(self):
        self.assertEqual(parse_size("10"), 10)
        self.assertEqual(parse_size("10K"), 10240)
        self.assertEqual(parse_size("1.5M"), int(1.5 * 1024**2))
        with self.assertRaises(ValueError):
            parse_size("nope")


if __name__ == "__main__":
    unittest.main()
