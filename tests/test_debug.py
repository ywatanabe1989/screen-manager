#!/usr/bin/env python3
"""Test script with ipdb debugging."""

def calculate(a, b):
    import ipdb; ipdb.set_trace()
    result = a + b
    print(f"Calculating: {a} + {b} = {result}")
    return result

def main():
    print("Starting calculation...")
    result = calculate(10, 20)
    print(f"Final result: {result}")

if __name__ == "__main__":
    main()