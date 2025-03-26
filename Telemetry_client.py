import grpc
import threading
import host_pb2
import host_pb2_grpc

class TelemetryClient:
    def __init__(self, client_id="telemetry"):
        self.client_id = client_id
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = host_pb2_grpc.HostControlStub(self.channel)
        self._running = False
        self._stop_event = threading.Event()
        self.message_queue = []
        self.queue_lock = threading.Lock()
    
    def telemetry_stream(self):
        """Stream telemetry data based on user input"""
        # Initial message to establish the stream
        yield host_pb2.HostMessage(
            sender=self.client_id,
            recipient="dashboard",
            command="telemetry:connected"
        )
        
        while not self._stop_event.is_set():
            # Check if there are messages to send
            with self.queue_lock:
                if self.message_queue:
                    command = self.message_queue.pop(0)
                    message = host_pb2.HostMessage(
                        sender=self.client_id,
                        recipient="dashboard",
                        command=f"telemetry:{command}"
                    )
                    print(f"[Telemetry] Sending: {message.command}")
                    yield message
    
    def process_responses(self, response_iterator):
        """Process any responses from the server"""
        for response in response_iterator:
            print(f"[Telemetry] Received from {response.sender}: {response.command}")
    
    def input_loop(self):
        """Handle user input from terminal"""
        print("[Telemetry] Enter telemetry data (e.g., 'speed=50,temp=75'):")
        print("[Telemetry] Type 'exit' to quit")
        
        while not self._stop_event.is_set():
            try:
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    self.stop()
                    break
                
                # Add the user input to the message queue
                with self.queue_lock:
                    self.message_queue.append(user_input)
            except EOFError:
                break
    
    def start(self):
        """Start the telemetry client"""
        self._running = True
        self._stop_event.clear()
        print(f"[Telemetry] Client starting with ID: {self.client_id}")
        
        # Start input thread
        input_thread = threading.Thread(target=self.input_loop)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            # Start bidirectional streaming
            responses = self.stub.TelemetryStream(self.telemetry_stream())
            self.process_responses(responses)
        except grpc.RpcError as e:
            print(f"[Telemetry] RPC error: {e}")
        finally:
            self._running = False
            self.channel.close()
    
    def stop(self):
        """Stop the telemetry client"""
        self._stop_event.set()
        print("[Telemetry] Client stopping...")

if __name__ == "__main__":
    client = TelemetryClient()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()