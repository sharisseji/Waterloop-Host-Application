import grpc
import host_pb2
import host_pb2_grpc
import threading

def send_telemetry(stub):
    """Continuously sends telemetry data."""
    def generator():
        while True:
            status = input("[Telemetry] Enter status update: ")
            yield host_pb2.HostMessage(sender="Telemetry", recipient="Dashboard", command=status)

    for _ in stub.TelemetryStream(generator()):
        pass

def telemetry_client():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = host_pb2_grpc.HostControlStub(channel)

        telemetry_thread = threading.Thread(target=send_telemetry, args=(stub,))
        telemetry_thread.start()
        telemetry_thread.join()

if __name__ == '__main__':
    telemetry_client()
