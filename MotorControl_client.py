# TEST.PY
import grpc
import host_pb2
import host_pb2_grpc
import time

def motor_control_client():
    while True:
        try:
            with grpc.insecure_channel('localhost:50051') as channel:
                stub = host_pb2_grpc.HostControlStub(channel)

                # print("[Motor Control] Listening for commands...")

                # this is not working
                for message in stub.MotorControlStream(iter([])):  # Keep listening
                    print(f"[Motor Control] Received command: {message.command}")
        except grpc.RpcError as e:
            print(f"[Motor Control] Disconnected: {e}, reconnecting in 5s...")
            time.sleep(5)  # Wait before reconnecting


if __name__ == '__main__':
    motor_control_client()

