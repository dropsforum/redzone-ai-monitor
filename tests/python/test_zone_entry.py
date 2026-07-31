import unittest

from ai_motion_app.zone_entry import classify_foot_point


class ZoneEntryTests(unittest.TestCase):
    def setUp(self):
        self.zone = [
            (0.25, 0.25),
            (0.75, 0.25),
            (0.75, 0.75),
            (0.25, 0.75),
        ]

    def test_uses_bottom_center_as_floor_contact(self):
        contact = classify_foot_point(
            x1=40,
            x2=60,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
        )
        self.assertEqual((50.0, 70.0), (contact.foot_x, contact.foot_y))
        self.assertTrue(contact.inside)

    def test_outside_foot_point_can_be_near_zone(self):
        contact = classify_foot_point(
            x1=40,
            x2=60,
            y2=80,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
        )
        self.assertFalse(contact.inside)
        self.assertTrue(contact.near)
        self.assertEqual(5.0, contact.distance_px)

    def test_far_foot_point_is_clear(self):
        contact = classify_foot_point(
            x1=0,
            x2=10,
            y2=95,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
        )
        self.assertFalse(contact.inside)
        self.assertFalse(contact.near)

    def test_warning_buffer_uses_normalized_geometry_on_widescreen_frames(self):
        zone = [(0.4, 0.4), (0.6, 0.4), (0.6, 0.8), (0.4, 0.8)]
        contact = classify_foot_point(
            450,
            550,
            160,
            zone,
            frame_width=1000,
            frame_height=500,
            warning_buffer=0.1,
        )

        self.assertFalse(contact.inside)
        self.assertTrue(contact.near)


if __name__ == "__main__":
    unittest.main()
