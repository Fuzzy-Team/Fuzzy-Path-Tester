#original by probably_ichigo, converted by chillketchup

size = 1/6

self.keyboard.press(rotup)
self.keyboard.press(rotup)
self.keyboard.press(rotup)
self.keyboard.press(rotup)

self.keyboard.walk(rightkey, 5 * size)
self.keyboard.walk(fwdkey, 5 * size)
self.keyboard.walk(leftkey, 15 * size)
self.keyboard.multiWalk([rightkey, backkey], 5 * size)

for i in range(width):
    self.keyboard.walk(backkey, 8 * size)
    self.keyboard.walk(rightkey, 2 * size)
    self.keyboard.walk(fwdkey, 8 * size)
    self.keyboard.walk(rightkey, 2 * size)
    self.keyboard.walk(backkey, 8 * size)
    self.keyboard.walk(rightkey, 2 * size)
    self.keyboard.walk(fwdkey, 8 * size)
    self.keyboard.walk(rightkey, 2 * size)
    self.keyboard.walk(backkey, 8 * size)
    self.keyboard.multiWalk([leftkey, fwdkey], 12 * size)
