#!/usr/bin/env python3
"""Offline regression tests for the VK repeats updater."""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_repeats as UR


class ResolveOwnerTests(unittest.TestCase):
    def test_uses_groups_get_by_id_when_utils_method_is_unavailable(self):
        calls = []

        def fake_vk(method, token, **params):
            calls.append((method, params))
            if method == "utils.resolveScreenName":
                raise RuntimeError(
                    "VK API utils.resolveScreenName: Method is not available for this profile type"
                )
            if method == "groups.getById":
                self.assertEqual(params["group_id"], "btv_restored")
                return [{"id": 232964863, "name": "BRIDGE TV"}]
            self.fail("Unexpected VK method: " + method)

        logs = []
        with patch.object(UR, "_vk", side_effect=fake_vk):
            result = UR._resolve("fake-token", "@btv_restored", logs.append)

        self.assertEqual(result, -232964863)
        self.assertEqual([c[0] for c in calls], ["utils.resolveScreenName", "groups.getById"])
        self.assertTrue(any("groups.getById" in line for line in logs))

    def test_uses_users_get_if_community_lookup_does_not_find_alias(self):
        def fake_vk(method, token, **params):
            if method == "utils.resolveScreenName":
                raise RuntimeError("method unavailable")
            if method == "groups.getById":
                raise RuntimeError("not a community")
            if method == "users.get":
                self.assertEqual(params["user_ids"], "btv_owner")
                return [{"id": 36245613, "first_name": "BTV", "last_name": "Owner"}]
            self.fail("Unexpected VK method: " + method)

        with patch.object(UR, "_vk", side_effect=fake_vk):
            result = UR._resolve("fake-token", "@btv_owner", lambda _: None)

        self.assertEqual(result, 36245613)

    def test_unresolvable_alias_does_not_block_numeric_owner_and_duplicates_are_removed(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            logs = []

            def fake_resolve(token, owner, log):
                if owner == "@unavailable":
                    raise RuntimeError("screen-name lookup unavailable")
                return -232964863

            video = {
                "owner_id": -232964863,
                "id": 12345,
                "title": "Test broadcast",
                "date": 1700000000,
            }
            with patch.object(UR, "_resolve", side_effect=fake_resolve), \
                 patch.object(UR, "_fetch_all", side_effect=lambda token, owner, log: calls.append(owner) or [video]):
                count, changed = UR.update_repeats(
                    "fake-token", root, "-232964863,@unavailable,@btv_restored", 48, log=logs.append
                )

            self.assertEqual(count, 1)
            self.assertTrue(changed)
            self.assertEqual(calls, [-232964863])
            self.assertTrue(any("пропущен" in line for line in logs))
            with open(os.path.join(root, "repeats.json"), encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(len(saved["items"]), 1)
            self.assertEqual(saved["items"][0]["id"], 12345)

    def test_all_unresolvable_owners_leave_existing_json_untouched(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "repeats.json")
            original = '{"items":[{"oid":-1,"id":77,"title":"Keep me","date":1,"embed":"https://vkvideo.ru/video_ext.php?oid=-1&id=77&hd=4"}]}\n'
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)

            with patch.object(UR, "_resolve", side_effect=RuntimeError("no access")):
                with self.assertRaisesRegex(RuntimeError, "Не удалось определить ни одного владельца"):
                    UR.update_repeats("fake-token", root, "@first,@second", 48, log=lambda _: None)

            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), original)


class LiveRecordingTests(unittest.TestCase):
    def test_finished_livestream_with_duration_is_not_treated_as_live_now(self):
        item = {
            "owner_id": -232964863,
            "id": 456239099,
            "title": "Finished BTV broadcast",
            "date": 1792262219,
            "live": 1,
            "duration": 7200,
        }
        self.assertFalse(UR._is_unfinished_live(item))

    def test_live_status_started_is_still_skipped(self):
        item = {"live": 1, "duration": 0, "live_status": "started"}
        self.assertTrue(UR._is_unfinished_live(item))

    def test_upcoming_flag_is_still_skipped(self):
        item = {"live": 1, "upcoming": 1, "duration": 0}
        self.assertTrue(UR._is_unfinished_live(item))

    def test_finished_livestream_is_written_to_repeats_json(self):
        with tempfile.TemporaryDirectory() as root:
            logs = []
            item = {
                "owner_id": -232964863,
                "id": 456239099,
                "title": "Finished BTV broadcast",
                "date": 1792262219,
                "live": 1,
                "duration": 7200,
            }
            with patch.object(UR, "_resolve", return_value=-232964863), \
                 patch.object(UR, "_fetch_all", return_value=[item]):
                count, changed = UR.update_repeats(
                    "fake-token", root, None, 48, log=logs.append
                )
            self.assertEqual(count, 1)
            self.assertTrue(changed)
            self.assertFalse(any("эфир ещё идёт" in line for line in logs))
            with open(os.path.join(root, "repeats.json"), encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["items"][0]["id"], 456239099)

    def test_default_owner_is_the_known_numeric_community_id(self):
        self.assertEqual(UR.DEFAULT_OWNER, "-232964863")
        self.assertEqual(UR._owners(None), [-232964863])


if __name__ == "__main__":
    unittest.main(verbosity=2)
