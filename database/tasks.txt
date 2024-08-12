import multiprocessing, time

MAX_RETRY = 10

def producer(q):
    for i in range(MAX_RETRY):
        print('producer', i)
        # send data queue
        # Do something before send the data
        q.put(i)
        time.sleep(1)
    



def consumer(q):
    while True:
        # There is data waiting
        if not q.empty():
            value = q.get()
            # Reach the final execution
            if value is None:
                break
            
            print('consumer', value)

            # Do something with the value
        time.sleep(2)
        


if __name__ == '__main__':
    # Create queue
    q = multiprocessing.Queue()

    productor_process = multiprocessing.Process(target=(producer), args=(q,))
    consumer_process = multiprocessing.Process(target=(consumer), args=(q,))
    
    # Start process
    productor_process.start()
    consumer_process.start()

    # wait to finished
    productor_process.join()
    # Signal to tell the consumer to stop
    q.put(None)

    
    consumer_process.join()