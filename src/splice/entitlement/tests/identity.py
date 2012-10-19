# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
import logging
import time

from splice.common import config, identity, rhic_serve_client, utils
from splice.common.identity import  create_or_update_consumer_identity, sync_from_rhic_serve, \
                                    sync_from_rhic_serve_blocking, SyncRHICServeThread
from splice.common.models import ConsumerIdentity, IdentitySyncInfo, RHICLookupTask

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)


class IdentityTest(BaseEntitlementTestCase):
    def setUp(self):
        super(IdentityTest, self).setUp()

    def tearDown(self):
        super(IdentityTest, self).tearDown()

    def test_get_all_rhics(self):
        rhics, meta = rhic_serve_client.get_all_rhics(host="localhost", port=0, url="mocked")
        self.assertEquals(len(rhics), 3)

    def test_sync_from_rhic_serve_blocking(self):
        self.assertEqual(len(identity.JOBS), 0)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)

    def test_sync_from_rhic_serve_threaded(self):
        self.assertEqual(len(identity.JOBS), 0)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_thread = sync_from_rhic_serve()
        for index in range(0,120):
            if not sync_thread.finished:
                time.sleep(.05)
        self.assertTrue(sync_thread.finished)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)

    def test_sync_where_existing_rhics_product_mapping_changes(self):
        self.assertEqual(len(identity.JOBS), 0)
        # Create a RHIC with products that will change after sync
        item = {}
        item["uuid"] = "fb647f68-aa01-4171-b62b-35c2984a5328"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)
            # Ensure that the products have been updated
        rhic_under_test = ConsumerIdentity.objects(uuid=item["uuid"]).first()
        self.assertTrue(rhic_under_test)
        expected_products = ["183", "83", "69"]
        for ep in expected_products:
            self.assertTrue(ep in rhic_under_test.engineering_ids)

    def test_get_current_rhic_lookup_tasks(self):
        cfg = config.get_rhic_serve_config_info()
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()

        # Ensure all tasks where created and have been saved in mongo
        current_tasks = [x.uuid for x in RHICLookupTask.objects()]
        for t in [task_a, task_b, task_c, task_d]:
            self.assertTrue(t.uuid in current_tasks)

        # In-progress, valid task
        task = identity.get_current_rhic_lookup_tasks(task_a.uuid)
        self.assertIsNotNone(task)
        self.assertEquals(task.uuid, task_a.uuid)

        # Completed, valid task
        task = identity.get_current_rhic_lookup_tasks(task_b.uuid)
        self.assertIsNotNone(task)
        self.assertEquals(task.uuid, task_b.uuid)

        # In-progress, timed out task
        task = identity.get_current_rhic_lookup_tasks(task_c.uuid)
        self.assertIsNone(task)
        found = [x.uuid for x in RHICLookupTask.objects()]
        self.assertTrue(task_c.uuid not in found)

        # Completed, cache time expired task
        task = identity.get_current_rhic_lookup_tasks(task_d.uuid)
        self.assertIsNone(task)
        found = [x.uuid for x in RHICLookupTask.objects()]
        self.assertTrue(task_d.uuid not in found)

        # Be sure of the 4 tasks we created, the expired and timedout were removed
        # while the 2 good tasks remained
        self.assertEquals(len(found), 2)
        self.assertTrue(task_a.uuid in found)
        self.assertTrue(task_b.uuid in found)

    def test_is_rhic_lookup_task_expired(self):
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        self.assertFalse(identity.is_rhic_lookup_task_expired(task_a))

        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        self.assertFalse(identity.is_rhic_lookup_task_expired(task_b))

        # Create a timedout incomplete task
        cfg = config.get_rhic_serve_config_info()
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        self.assertTrue(identity.is_rhic_lookup_task_expired(task_c))

        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()
        self.assertTrue(identity.is_rhic_lookup_task_expired(task_d))


    def test_purge_expired_rhic_lookups(self):
        cfg = config.get_rhic_serve_config_info()
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()

        identity.purge_expired_rhic_lookups()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 2)
        for f in found:
            self.assertTrue(f.uuid in [task_a.uuid, task_b.uuid])
            self.assertTrue(f.uuid not in [task_c.uuid, task_d.uuid])

    def test_get_in_progress_rhic_lookups(self):
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        cfg = config.get_rhic_serve_config_info()
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        current_tasks = identity.get_in_progress_rhic_lookups()
        self.assertEquals(len(current_tasks), 1)
        self.assertEquals(current_tasks[0].uuid, task_a.uuid)

    def test_delete_rhic_lookup(self):
        self.assertFalse(identity.delete_rhic_lookup(None))

        task = RHICLookupTask(uuid=self.dummy_uuid)
        task.save()
        self.assertTrue(identity.delete_rhic_lookup(task))
        self.assertEquals(len(RHICLookupTask.objects()), 0)

    def test_simulate_multiple_sync_threads_at_sametime(self):
        # Simulate a syncthread was created and hasn't finished yet
        key = SyncRHICServeThread.__name__
        # Skipping lock on identity.JOBS
        dummy_job = SyncRHICServeThread()
        identity.JOBS[key] = dummy_job
        # This thread is not in a finished state, therefore next job we try to create should return None
        # and do nothing, letting this job finish
        sync_thread = sync_from_rhic_serve()
        self.assertIsNone(sync_thread)
        # Now we simulate the job finishing and cleaning up it's reference
        dummy_job.remove_reference()
        # Ensure JOBS has been cleanedup
        self.assertEqual(len(identity.JOBS), 0)

    def test_create_new_consumer_identity(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])

    def test_update_consumer_identity(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        self.assertEquals(len(rhics[0].engineering_ids), 2)
        # Add a product to engineering ids and update
        item["engineering_ids"] += "3"
        self.assertNotEquals(rhics[0].engineering_ids, item["engineering_ids"])
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        self.assertEquals(len(rhics[0].engineering_ids), 3)


    def test_update_consumer_that_has_been_marked_as_deleted(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        item["deleted"] = True
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertTrue(rhics[0].deleted)

    def test_get_last_sync_timestamp(self):
        server_hostname = "a.b.c.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()

        found = identity.get_last_sync_timestamp(server_hostname)
        self.assertIsNotNone(found)
        created = sync_info.last_sync
        self.assertEquals(created.year, found.year)
        self.assertEquals(created.month, found.month)
        self.assertEquals(created.day, found.day)
        self.assertEquals(created.hour, found.hour)
        self.assertEquals(created.minute, found.minute)
        self.assertEquals(created.second, found.second)

    def test_save_duplicate(self):
        server_hostname = "simple.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()
        self.assertEquals(len(IdentitySyncInfo.objects()), 1 )

        dup = IdentitySyncInfo(server_hostname=server_hostname)
        dup.last_sync = datetime.now(tzutc())
        caught = False
        try:
            dup.save()
        except:
            caught = True
        data =  IdentitySyncInfo.objects()
        self.assertEquals(len(data), 1)
        self.assertTrue(caught)

    def test_save_last_sync(self):
        server_hostname = "a.b.c.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()
        key = utils.sanitize_key_for_mongo(server_hostname)
        lookup = IdentitySyncInfo.objects(server_hostname=key)
        self.assertIsNotNone(lookup)
        self.assertEquals(len(lookup), 1)
        created = sync_info.last_sync
        found = lookup[0].last_sync
        self.assertEquals(created.year, found.year)
        self.assertEquals(created.month, found.month)
        self.assertEquals(created.day, found.day)
        self.assertEquals(created.hour, found.hour)
        self.assertEquals(created.minute, found.minute)
        self.assertEquals(created.second, found.second)
