#original by ichigo, converted by chillketchup

size = 1/6

self.keyboard.press(rotup)
self.keyboard.press(rotup)
self.keyboard.press(rotup)
self.keyboard.press(rotup)

self.keyboard.walk(rightkey, 5 * size)
self.keyboard.walk(fwdkey, 5 * size)

for i in range(width):
    self.keyboard.walk(leftkey, 8 * size)
    #sleep(0.05)

    self.keyboard.multiWalk([rightkey, backkey], 11 * size)
    #sleep(0.05)

    self.keyboard.walk(leftkey, 8 * size)
    #sleep(0.05)

    self.keyboard.walk(fwdkey, 2 * size)
    #sleep(0.05)

    self.keyboard.walk(rightkey, 8 * size)
    #sleep(0.05)

    self.keyboard.walk(fwdkey, 2 * size)
    #sleep(0.05)

    self.keyboard.walk(leftkey, 8 * size)
    #sleep(0.05)

    self.keyboard.walk(fwdkey, 2 * size)
    #sleep(0.05)

    self.keyboard.walk(rightkey, 8 * size)
    #sleep(0.05)

    self.keyboard.walk(fwdkey, 2 * size)
    #sleep(0.05)

