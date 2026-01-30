self.keyboard.press("a", 0.8)
self.keyboard.press("s", 1.1*size)
self.keyboard.press("d", 0.4)

for _ in range(4):
    self.keyboard.walk("w", 0.3*size)

for _ in range(2):
    self.keyboard.walk("d", 0.4*width)
    self.keyboard.walk("s", 0.25*size)
    self.keyboard.walk("a",0.4*width)
    self.keyboard.walk("s",0.25*size)

self.keyboard.walk("d", 0.4*width)
self.keyboard.walk("s", 0.25*size)
self.keyboard.walk("a",0.4*width)

for _ in range(4):
    self.keyboard.walk("w", 0.25*size)

for _ in range(2):
    self.keyboard.walk("d", 0.4*width)
    self.keyboard.walk("s", 0.25*size)
    self.keyboard.walk("a",0.4*width)
    self.keyboard.walk("s",0.25*size)

for _ in range(2):
    self.keyboard.walk("d", 0.3*width)
    self.keyboard.walk("w", 0.15*size)
    self.keyboard.walk("a",0.3*width)
    self.keyboard.walk("w",0.15*size)