if sizeword.lower() == "xs":
    size = 0.5
elif sizeword.lower() == "s":
    size = 1
elif sizeword.lower() == "l":
    size = 2
elif sizeword.lower() == "xl":
    size = 2.5
else:
    size = 1.5 

self.keyboard.walk(leftkey, 4 * size)
self.keyboard.walk(fwdkey, 4 * size)

for i in range(2):
    self.keyboard.walk(backkey, 0.5 * size)
    self.keyboard.walk(leftkey, 1 * size)
    self.keyboard.walk(fwdkey, 1 * size )
    self.keyboard.tileWalk(rightkey, 4 * size)
    self.keyboard.tileWalk(backkey, 5 * size)
    self.keyboard.tileWalk(leftkey, 1 * size)
    self.keyboard.tileWalk(fwdkey, 3)

self.keyboard.walk(fwdkey, 2 * size)
self.keyboard.walk(leftkey, 2 * size)

for i in range(2):
    self.keyboard.walk(leftkey, 1 * size)
    self.keyboard.walk(fwdkey, 1 * size)
    self.keyboard.tileWalk(rightkey, 4 * size)
    self.keyboard.tileWalk(backkey, 5 * size)
    self.keyboard.tileWalk(leftkey, 4 * size)
    self.keyboard.tileWalk(fwdkey, 2 * size)

self.keyboard.walk(leftkey, 1 * size)
self.keyboard.walk(fwdkey, 1 * size)

for i in range(2):
    self.keyboard.walk(rightkey, 0.5 * size)
    self.keyboard.multiWalk([backkey, rightkey], 0.5 * size)
    self.keyboard.walk(leftkey, 0.25)
    self.keyboard.walk(fwdkey, 0.25)
    
self.keyboard.walk(leftkey, 4 * size)
self.keyboard.walk(fwdkey, 4 * size)

for i in range(2):
    self.keyboard.walk(rightkey, 0.5 * size)
    self.keyboard.multiWalk([backkey, rightkey], 0.5 * size)
    self.keyboard.walk(leftkey, 0.25)
    self.keyboard.walk(fwdkey, 0.25)
