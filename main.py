import os

print(""" FiveM-Checkpoint-Hunter-Options (Q to quit): 
(1): (Faster-but-Messy)
(2): (Slower-but-Precise)
(3): (Faster-but-Messy-Winter)""")

c = input("Choose your option number: ").strip().lower()

if c == "1":   os.system("python3 1.py")
elif c == "2": os.system("python3 2.py")
elif c == "3": os.system("python3 3.py")
elif c == "q": print("bye"); os._exit(0)
else: print("I don't have that option")