#!/usr/bin/env python
from __future__ import print_function
from multiprocessing import Process, Queue, cpu_count
from PIL import Image, ImageSequence
import time, sys, images2gif

class Chunk:
    def __init__(self, id):
        self.id = id
        self.data = []
    def digest(self):
        return map(lambda img: img.load(), self.data)

def load_sequence(filename):
    """ 
    Takes the name of an image sequence
    Returns a list of frames
    """
    # Would it be worth it to add multiprocessing to this too?
    frames = []
    sequence = Image.open(filename)
    try:
        while 1:
            frame = Image.new("RGBA", sequence.size) 
            frame.paste(sequence) # copies each frame into a new image
            frames.append(frame)
            sequence.seek(sequence.tell()+1) # go to next frame
    except EOFError: 
        pass
    return frames
        
def create_image_chunks(frames, number_of_chunks):
    """
    Takes a list of frames
    Returns a list of chunks for multiprocessing
    """
    # create n chunks from the source rectangle by dividing the source into n rectangles
    width, height = frames[0].size
    chunks = []
    chunk_width = int(width/number_of_chunks)

    for n in range(number_of_chunks):
        chunk = Chunk(n)
        for frame in frames:
            # slice each frame into a rectangle and add it to the chunk
            box = (n*chunk_width, 0, n*chunk_width+chunk_width, height)
            region = frame.crop(box)
            img = Image.new("RGBA", [chunk_width, height])
            img.paste(region, (0,0))
            chunk.data.append(img)
        chunks.append(chunk)
    return chunks

def dechunkify(chunks):
    """
    Takes a list of chunks and reconstructs the image sequence
    Returns a list of images
    """
    print("dechunking framebuffer...")
    number_of_frames = len(chunks[0].data)
    chunk_count = len(chunks)
    chunk_width, chunk_height = chunks[0].data[0].size[0], chunks[0].data[0].size[1]
    final_width, final_height = chunk_width*chunk_count, chunk_height
    frames = []
    for framedepth in range(number_of_frames):
        frame = Image.new("RGBA", [final_width, final_height])
        for n in range(len(chunks)):
            frame_chunk = chunks[n].data[framedepth]
            region = frame_chunk.copy()
            frame.paste(region, (n*chunk_width,0))
        frames.append(frame)
    return frames

def worker(input_queue, output_queue):
    chunk = input_queue.get()
    pixels = []
    width, height = chunk.data[0].size
    data = chunk.digest() # process into pixel data

    depth = len(data)
    print("worker",chunk.id, ": transdimensional probe : ", width, height, depth)
    # return
    print("worker", chunk.id, ": beginning time cube fabrication...")

    # Create the time cube
    for x in range(width): # yay exponential time!
        pixels.append([])
        for y in range(height):
            pixels[x].append([])
            for z in range(depth):
                pixels[x][y].append(data[z][x, y])

    # Column sort!
    print("worker", chunk.id, ": sortulating columnulars...")
    for x in range(width):
        for y in range(height):
            pixels[x][y] = sorted(pixels[x][y])
    
    # Frame reconstruction
    print("worker", chunk.id, ": reconstructing frames...")
    frames = []
    for n in range(len(data)):
        frame = data[n]
        for x in range(width):
            for y in range(height):
                frame[x,y] = pixels[x][y][n]
        new_im = Image.new("RGBA", [width,height])
        new_im.paste(chunk.data[n])
        frames.append(new_im)
    output = Chunk(chunk.id)
    output.data = frames
    output_queue.put(output) # return it to the main process
    print("finished processing chunk", chunk.id, "...")

def process_chunks(chunks, should_reverse_chunks):
    """
    Spawn a worker process for each chunk to do the magic stuff
    """
    processed = []
    workers = []
    in_queue = Queue()
    for chunk in chunks: in_queue.put(chunk)
    out_queue = Queue()

    for chunk in chunks:
        p = Process(target=worker, args=(in_queue,out_queue))
        print("initializing processor for chunk", chunk.id, "...")
        p.start()
        workers.append(p)

    for x in range(len(chunks)):
        processed.append(out_queue.get()) 

    processed.sort(lambda a, b: cmp(a.id, b.id), reverse=should_reverse_chunks)
    print(map(lambda c:c.id, processed))
    return processed

def read_args():
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Error: please specify a file name")
        sys.exit()
    return filename

if __name__ == '__main__':
    
    filename = read_args()
    start = time.time()
    # load the .gif file as an image sequence sequence
    frames = load_sequence(filename) 
    # split the sequence into chunks for multiprocessing
    chunks = create_image_chunks(frames, number_of_chunks=cpu_count()*2) # should check for hyperthreading?
    # distribute chunks to subprocesses
    processed = process_chunks(chunks, should_reverse_chunks=False)
    # recombine procesed pieces
    result = dechunkify(processed)
    images2gif.writeGif("derp.gif", result , 0.04)
    end = time.time()
    elapsed = '%.2f' % (end - start)
    print('Chronofucked in ' + elapsed + ' seconds!')

