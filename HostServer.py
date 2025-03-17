import grpc
from concurrent import futures
import host_pb2
import host_pb2_grpc
import threading

class HostControlServicer(host_pb2_grpc.HostControlServicer):
    def __init__(self):
        self.telemetry_subscribers = []
        self.command_subscribers = []
        self.motor_control_subscribers = []  # NEW: Motor Control clients
        self.lock = threading.Lock()

    # Telemetry works as before: do NOT TOUCH the Telemetry Stream or Telemetry_client.py
    def TelemetryStream(self, request_iterator, context):
        with self.lock:
            self.telemetry_subscribers.append(context)
            
        try:
            for message in request_iterator:
                print(f"[Server] Received telemetry: {message.command}")
                with self.lock:
                    for subscriber in self.telemetry_subscribers:
                        if subscriber.is_active():
                            yield message  # Send to Dashboard
        except grpc.RpcError:
            pass

    # Server routing from Dashboard: receiving works, sending does not work
    def CommandStream(self, request_iterator, context):
        with self.lock:
            self.command_subscribers.append(context)

        try:
            for message in request_iterator:
                print(f"[Server] Received motor command from Dashboard: {message.command}")

                # Send this command to Motor Control
                with self.lock:
                    for subscriber in self.motor_control_subscribers:
                        if subscriber.is_active():
                            print(f"[Server] Forwarding command to Motor Control: {message.command}")
                            yield message  # Send to Motor Control
        except grpc.RpcError:
            pass

    # Attempt to implement a separate bidirectional stream for Motor Control
    # does not work: likely because the server cannot simultaneously manage requests and responses in addition to bidirectional streams
    def MotorControlStream(self, request_iterator, context):
        with self.lock:
            self.motor_control_subscribers.append(context)

        try:
            for message in request_iterator:
                print(f"[Server] Motor Control Stream received: {message.command}")
                with self.lock:
                    for subscriber in self.motor_control_subscribers:
                        if subscriber.is_active():
                            yield message  # Send to all Motor Control clients
        except grpc.RpcError:
            pass

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    host_pb2_grpc.add_HostControlServicer_to_server(HostControlServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
