"""Every cell of OpenAPI 3.1.1 section 4.8.12.4 (Style Examples). Author: Sandeep Belgavi."""
import unittest
from serialize import serialize

S, A, O = "blue", ["blue", "black", "brown"], {"R": 100, "G": 200, "B": 150}
# (style, explode): (undefined, string, array, object); None means n/a in the spec.
TABLE = {
    ("matrix", False): (";color", ";color=blue", ";color=blue,black,brown", ";color=R,100,G,200,B,150"),
    ("matrix", True): (";color", ";color=blue", ";color=blue;color=black;color=brown", ";R=100;G=200;B=150"),
    ("label", False): (".", ".blue", ".blue,black,brown", ".R,100,G,200,B,150"),
    ("label", True): (".", ".blue", ".blue.black.brown", ".R=100.G=200.B=150"),
    ("simple", False): ("", "blue", "blue,black,brown", "R,100,G,200,B,150"),
    ("simple", True): ("", "blue", "blue,black,brown", "R=100,G=200,B=150"),
    ("form", False): ("color=", "color=blue", "color=blue,black,brown", "color=R,100,G,200,B,150"),
    ("form", True): ("color=", "color=blue", "color=blue&color=black&color=brown", "R=100&G=200&B=150"),
    ("spaceDelimited", False): (None, None, "color=blue%20black%20brown", "color=R%20100%20G%20200%20B%20150"),
    ("spaceDelimited", True): (None, None, None, None),
    ("pipeDelimited", False): (None, None, "color=blue%7Cblack%7Cbrown", "color=R%7C100%7CG%7C200%7CB%7C150"),
    ("pipeDelimited", True): (None, None, None, None),
    ("deepObject", False): (None, None, None, None),
    ("deepObject", True): (None, None, None, "color%5BR%5D=100&color%5BG%5D=200&color%5BB%5D=150"),
}


class SpecTableTest(unittest.TestCase):
    def test_every_cell(self):
        checked = 0
        for (style, explode), row in TABLE.items():
            for value, expected in zip((None, S, A, O), row):
                with self.subTest(style=style, explode=explode, value=value):
                    if expected is None:
                        with self.assertRaises(ValueError):
                            serialize("color", value, style, explode)
                    else:
                        self.assertEqual(serialize("color", value, style, explode), expected)
                        checked += 1
        self.assertEqual(checked, 37)

    def test_query_default_is_form_explode(self):
        self.assertEqual(serialize("color", A), "color=blue&color=black&color=brown")

    def test_path_default_is_simple(self):
        self.assertEqual(serialize("color", A, location="path"), "blue,black,brown")

    def test_commas_inside_values_are_encoded(self):
        self.assertEqual(serialize("tag", ["a,b", "c"], "form", False), "tag=a%2Cb,c")


if __name__ == "__main__":
    unittest.main()
