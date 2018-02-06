## Project: fair-fed
A convolutional neural network based image classifier used to solve a tricky problem of feeding birds selectively.  

## Problem
At a bird feeder observed that crows were over powering pigeons and were not letting them come inside bird feeder to eat. Don't know the exact reason why but after a point it looked as if they were scaring off pigeons for fun after being full. Hmmm... let's see if we can help pigeons.

## Solution
Scare off crows and also, hide food when crows are around. If pigeons(or any other birds) are there let them eat.

Thought of putting up a simple approach of using convolutional neural networks to precisely identify bird @ bird feeder and trigger a set of hardware to accomplish selective feeding.

So, Neural N/W identifies bird in view, if it's crow, a python application is used to make noise, trigger motor attached to RPi3 which retracts feeding tray and keeps scanning images of view to make sure this state is maintained till crows have flown away.

## Code walk through (Work in progress)

[classifier_server.py](classifier_server.py)

[pi_module.py](pi_module.py)

