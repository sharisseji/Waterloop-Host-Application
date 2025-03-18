import grpc
import threading
import host_pb2
import host_pb2_grpc

class MotorControlClient:
    def __init__(self, client_id="motor_control"):
        self.client_id = client_id
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = host_pb2_grpc.HostControlStub(self.channel)
        self._running = False
        self._stop_event = threading.Event()
    
    def empty_stream(self):
        """Generate an initial message to establish the stream"""
        # Send only an initial message to establish the connection
        yield host_pb2.HostMessage(
            sender=self.client_id,
            recipient="server",
            command="initialized"
        )
        
        # Keep the client connection alive
        while not self._stop_event.is_set():
            # We don't send additional messages in this implementation
            # But we need to keep the generator alive
            if self._stop_event.wait(10):  # Check stop flag every 10 seconds
                break
    
    def process_commands(self, response_iterator):
        """Process command messages from the server (from dashboard)"""
        print("[Motor] Waiting for commands...")
        for response in response_iterator:
            if response.sender == "dashboard" and response.command.startswith("motor:"):
                command_data = response.command.replace("motor:", "")
                print(f"[Motor] Received command: {command_data}")
                print("[Motor] Executing motor command...")
                # Here you would actually execute the motor command
                # For example: self.execute_motor_command(command_data)
    
    def start(self):
        """Start the motor control client"""
        self._running = True
        self._stop_event.clear()
        print(f"[Motor] Client starting with ID: {self.client_id}")
        
        try:
            # Start bidirectional streaming but only care about responses
            responses = self.stub.MotorControlStream(self.empty_stream())
            self.process_commands(responses)
        except grpc.RpcError as e:
            print(f"[Motor] RPC error: {e}")
        finally:
            self._running = False
            self.channel.close()
    
    def stop(self):
        """Stop the motor control client"""
        self._stop_event.set()
        print("[Motor] Client stopping...")

if __name__ == "__main__":
    client = MotorControlClient()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()