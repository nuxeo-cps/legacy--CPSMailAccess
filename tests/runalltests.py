#
# Runs all tests in the current directory
#
# Execute like:
#   python runalltests.py
#
# Alternatively use the testrunner: 
#   python /path/to/Zope/utilities/testrunner.py -qa
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py')) 

import unittest, doctest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

tests = os.listdir(os.curdir)
tests = [n[:-3] for n in tests if n.startswith('test') and n.endswith('.py')]

for test in tests:
    m = __import__(test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())       

for test in tests:
    m = __import__(test)   
    
# running doctests    
tests = os.listdir(os.curdir)
doctest_list = [n[:-3] for n in tests if n.startswith('doc_test') and n.endswith('.py')]

doc_suites = []

for test in doctest_list:
    m = __import__(test)
    if hasattr(m, 'doc_testSuite'):
        for doctestable in m.doc_testSuite    ():
            doc_suite = doctest.DocTestSuite(doctestable)  
            doc_suites.append(doc_suite)
    
if __name__ == '__main__':
    TestRunner().run(suite)
    
    for doc_suite in doc_suites:
        TestRunner().run(doc_suite)

