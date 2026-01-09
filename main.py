import sys

print(""" 
FiveM-Checkpoint-Hunter-Options: 
(1): Faster-but-Messy
(2): Slower-but-Precise
(3): Faster-but-Messy-Winter
""")

c = input("Choose your option number then press enter (Q to quit): ").strip().lower()

if c == "1":
    from modes import m1
    m1.main()
elif c == "2":
    from modes import m2
    m2.main()
elif c == "3":
    from modes import m3
    m3.main()
elif c == "q":
    sys.exit(0)
else:
    print("Invalid option.")