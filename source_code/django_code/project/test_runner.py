import unittest
import logging
from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        # Redirect output to a file
        with open('test_output.log', 'w') as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=self.verbosity, failfast=self.failfast)
            result = runner.run(suite)
        return result