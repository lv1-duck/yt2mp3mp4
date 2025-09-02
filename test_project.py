import sys
sys.dont_write_bytecode = True
from project import dummy_function,dummy_function2,dummy_function3
import pytest

def test_dummy_function():
    assert dummy_function() == 2

def test_dummy_function2():
    assert dummy_function2() == 3

def test_dummy_function3():
    assert dummy_function3() == 4

def main():
    test_dummy_function()
    test_dummy_function2()
    test_dummy_function3()

main()
