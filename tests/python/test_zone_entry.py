import unittest

from ai_motion_app.zone_entry import classify_foot_point, classify_person_zone


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

    def test_mask_overlap_triggers_inside_when_bottom_center_is_outside(self):
        contact = classify_person_zone(
            x1=20,
            x2=80,
            y2=95,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
            mask_polygons=[[(40, 40), (60, 40), (60, 60), (40, 60)]],
        )

        self.assertTrue(contact.inside)
        self.assertTrue(contact.near)
        self.assertEqual("mask", contact.method)
        self.assertGreater(contact.overlap_ratio, 0.0)
        self.assertFalse(contact.position_uncertain)

    def test_bbox_overlap_does_not_trigger_when_mask_is_outside(self):
        contact = classify_person_zone(
            x1=20,
            x2=80,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.0,
            mask_polygons=[[(20, 30), (24, 30), (24, 70), (20, 70)]],
        )

        self.assertFalse(contact.inside)
        self.assertFalse(contact.near)
        self.assertEqual("mask", contact.method)
        self.assertEqual(0.0, contact.overlap_ratio)

    def test_full_body_without_mask_uses_footpoint(self):
        contact = classify_person_zone(
            x1=40,
            x2=60,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
        )

        self.assertTrue(contact.inside)
        self.assertEqual("footpoint", contact.method)
        self.assertFalse(contact.position_uncertain)

    def test_bottom_clipped_without_mask_is_uncertain_and_near(self):
        contact = classify_person_zone(
            x1=40,
            x2=60,
            y2=100,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
        )

        self.assertFalse(contact.inside)
        self.assertTrue(contact.near)
        self.assertEqual("bottom-cropped", contact.method)
        self.assertTrue(contact.position_uncertain)

    def test_tiny_mask_overlap_is_warning_not_breach(self):
        contact = classify_person_zone(
            x1=10,
            x2=50,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.0,
            mask_polygons=[[(10, 10), (26, 10), (26, 26), (10, 26)]],
            mask_overlap_threshold=0.05,
        )

        self.assertFalse(contact.inside)
        self.assertTrue(contact.near)
        self.assertGreater(contact.overlap_ratio, 0.0)

    def test_mask_within_contact_tolerance_counts_as_inside(self):
        contact = classify_person_zone(
            x1=10,
            x2=30,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
            mask_polygons=[[(10, 30), (24.5, 30), (24.5, 60), (10, 60)]],
            mask_contact_tolerance=0.01,
        )

        self.assertTrue(contact.inside)
        self.assertTrue(contact.near)
        self.assertEqual("mask", contact.method)

    def test_mask_beyond_warning_distance_is_clear(self):
        contact = classify_person_zone(
            x1=0,
            x2=10,
            y2=70,
            zone=self.zone,
            frame_width=100,
            frame_height=100,
            warning_buffer=0.10,
            mask_polygons=[[(0, 30), (10, 30), (10, 60), (0, 60)]],
        )

        self.assertFalse(contact.inside)
        self.assertFalse(contact.near)


if __name__ == "__main__":
    unittest.main()
