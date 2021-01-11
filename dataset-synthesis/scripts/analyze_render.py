filename = 'names.txt'
f = open(filename)
lines = f.readlines()

# dict storing id: [frame]
ids = {}
for line in lines:
    l = line
    l = l.replace('\n', '')
    l = l.replace('\t', '')
    frames = l.split()

    for frame in frames:
        obj = frame[:frame.index('-')]
        frameno = frame[frame.index('-') + 1: frame.index('.')]

        if obj in ids:
            if frameno in ids[obj]:
                print('duplicate frame for ' + obj + ': ' + frameno)
            else:
                tmp = ids[obj]
                tmp.append(int(frameno))
                ids[obj] = tmp
        else:
            ids[obj] = [int(frameno)]

missing_frames = []
frame_range = [x for x in range(3601)]
for k, v in ids.items():
    if len(v) != 3601:
        for frame in frame_range:
            if frame not in v:
                missing_frames.append((k, frame))
                break
                # print('obj ' + k + ' is missing frame ' + str(frame))
print(missing_frames)

f.close()
