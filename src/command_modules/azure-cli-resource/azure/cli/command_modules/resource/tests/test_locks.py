# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, record_only


class ResourceLockTests(ScenarioTest):
    def test_list_locks(self):
        # just make sure this doesn't throw
        self.cmd('az lock list').get_output_in_json()

    @record_only()
    def test_lock_create_list_delete(self):
        for lock_type in ['ReadOnly', 'CanNotDelete']:
            lock_name = self.create_random_name('cli-test-lock', 48)
            self.cmd('az lock create -n {} --lock-type {}'.format(lock_name, lock_type))
            self._sleep_for_lock_operation()

            locks_list = self.cmd('az lock list').get_output_in_json()
            self.assertTrue(locks_list)
            self.assertIn(lock_name, [l['name'] for l in locks_list])

            lock = self.cmd('az lock show -n {}'.format(lock_name)).get_output_in_json()
            self.assertEqual(lock.get('name', None), lock_name)
            self.assertEqual(lock.get('level', None), lock_type)

            self.cmd('az lock delete -n {}'.format(lock_name))
            self._sleep_for_lock_operation()

    @ResourceGroupPreparer(name_prefix='cli_test_readonly_resource_group_lock')
    def test_readonly_resource_group_lock(self, resource_group):
        self._lock_operation_with_resource_group('ReadOnly', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_cannotdelete_resource_group_lock')
    def test_cannotdelete_resource_group_lock(self, resource_group):
        self._lock_operation_with_resource_group('CanNotDelete', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_readonly_resource_lock')
    def test_readonly_resource_lock(self, resource_group):
        self._lock_operation_with_resource('ReadOnly', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_cannotdelete_resource_lock')
    def test_cannotdelete_resource_lock(self, resource_group):
        self._lock_operation_with_resource('CanNotDelete', resource_group)

    def _lock_operation_with_resource_group(self, lock_type, resource_group):
        lock_name = self.create_random_name('cli-test-lock', 48)

        self.cmd('az lock create -n {} -g {} --lock-type {}'.format(lock_name, resource_group, lock_type))
        self._sleep_for_lock_operation()

        self.cmd('az lock show -g {} -n {}'.format(resource_group, lock_name)).assert_with_checks([
            JMESPathCheck('name', lock_name),
            JMESPathCheck('level', lock_type)])

        locks_list = self.cmd("az lock list --query '[].name' -ojson").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        self.cmd('az lock delete -g {} -n {}'.format(resource_group, lock_name))
        self._sleep_for_lock_operation()

    def _lock_operation_with_resource(self, lock_type, resource_group):
        rsrc_name = self.create_random_name('cli.lock.rsrc', 30)
        rsrc_type = 'Microsoft.Network/virtualNetworks'
        lock_name = self.create_random_name('cli-test-lock', 74)

        self.cmd('az network vnet create -n {} -g {}'.format(rsrc_name, resource_group))
        self.cmd('az lock create -n {} --resource-type {} -g {} --resource-name {} --lock-type {}'
                 .format(lock_name, rsrc_type, resource_group, rsrc_name, lock_type))
        self._sleep_for_lock_operation()

        self.cmd('az lock show --name {} -g {} --resource-type {} --resource-name {}'
                 .format(lock_name, resource_group, rsrc_type, rsrc_name)).assert_with_checks([
                     JMESPathCheck('name', lock_name),
                     JMESPathCheck('level', lock_type)])

        locks_list = self.cmd("az lock list --query '[].name' -ojson").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        self.cmd('az lock delete --name {} -g {} --resource-name {} --resource-type {}'
                 .format(lock_name, resource_group, rsrc_name, rsrc_type))
        self._sleep_for_lock_operation()

    def _sleep_for_lock_operation(self):
        if self.is_live:
            sleep(5)


if __name__ == '__main__':
    unittest.main()
