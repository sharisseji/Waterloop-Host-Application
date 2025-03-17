import grpc
import host_pb2
import host_pb2_grpc
import threading
import queue

command_queue = queue.Queue()

def receive_telemetry_updates(stub):
    """Receives real-time telemetry updates."""
    for message in stub.TelemetryStream(iter([]), timeout = None):
        print(f"[Dashboard] Received telemetry: {message.command}")

def send_motor_commands(stub):
    """Sends motor commands."""
    def generator():
        while True:
            command = command_queue.get()
            yield host_pb2.HostMessage(sender="Dashboard", recipient="MotorControl", command=command)

    for _ in stub.CommandStream(generator()):
        pass

def dashboard_client():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = host_pb2_grpc.HostControlStub(channel)
        telemetry_thread = threading.Thread(target=receive_telemetry_updates, args=(stub,))
        command_thread = threading.Thread(target=send_motor_commands, args=(stub,))

        telemetry_thread.start()
        command_thread.start()
        while True:
            command = input("[Dashboard] Enter motor command: ")
            message = host_pb2.HostMessage(sender="Dashboard", recipient="MotorControl", command=command)
            stub.CommandStream(iter([message]))  # Send to server

if __name__ == '__main__':
    dashboard_client()