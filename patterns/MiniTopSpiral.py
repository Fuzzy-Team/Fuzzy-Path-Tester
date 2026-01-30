if sizeword.lower() == "xs":
    size = 0.5
elif sizeword.lower() == "s":
    size = 0.75
elif sizeword.lower() == "l":
    size = 1.25
elif sizeword.lower() == "xl":
    size = 1.5
else:
    size = 1

self.keyboard.walk(backkey, 3*size)
self.keyboard.walk(leftkey, 3*size)

self.keyboard.walk(fwdkey, 1*size)
self.keyboard.walk(rightkey, 1*size)
self.keyboard.walk(fwdkey, 0.2*size)

for i in range (5):
    self.keyboard.walk(fwdkey, 1*size)
    self.keyboard.walk(leftkey, 1*size)
    self.keyboard.walk(backkey, 1*size)
    self.keyboard.walk(rightkey, 1*size)





