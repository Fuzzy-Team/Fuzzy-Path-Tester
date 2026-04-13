from time import sleep

self.keyboard.press(".")
self.keyboard.walk("w", 1.2)
self.keyboard.multiWalk(["w", "d"], 0.7)
sleep(0.2)
self.keyboard.walk("a", 0.8)
self.keyboard.keyDown("s", False)
sleep(0.5)
self.keyboard.keyUp("s", False)
