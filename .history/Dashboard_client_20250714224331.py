# VERSION 10: with CAN
import can
import grpc
import threading
import host_pb2
import host_pb2_grpc
import logging
import random

class DashboardClient:
    def __init__(self, client_id="dashboard"):
        self.client_id = client_id
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = host_pb2_grpc.HostControlStub(self.channel)
        self._running = False
        self._stop_event = threading.Event()
        self.message_queue = []
        self.queue_lock = threading.Lock()
        
    def command_stream(self):
        """Generate motor commands based on user input"""
        # Initial message to establish the stream
        yield host_pb2.HostMessage(
            sender=self.client_id,
            recipient="motor_control",
            command="Dashboard connected" # this doesn't send to motor controller properly, but it isn't necessary
        )
        
        while not self._stop_event.is_set():
            # Check if there are messages to send
            with self.queue_lock:
                if self.message_queue:
                    command = self.message_queue.pop(0)
                    message = host_pb2.HostMessage(
                        sender=self.client_id,
                        recipient="motor_control",
                        command=command  # Command format is already prepared
                    )
                    print(f"[Dashboard] Sending CAN message: {command}") # command holds the motor control data
                    yield message
    
    def process_responses(self, response_iterator):
        """Process responses from the server (telemetry updates)"""
        for response in response_iterator:
            print(f"[Dashboard] Received from {response.sender}: {response.command}") # command holds the telemetry data
    
    def input_loop(self):
        """Handle user input from terminal"""
        print("[Dashboard] Commands:")
        print("1. Type 'random' to send a random CAN message")
        print("2. Type 'can:ID:DATA' where ID is CAN ID (0-2047) and DATA is comma-separated bytes")
        print("   Example: can:123:10,20,30,40,50,60,70,80")
        print("3. Motor Control Commands:")
        print("   - 'start:THROTTLE' to start motor (throttle 0-100)")
        print("   - 'stop' to stop motor")
        print("   - 'throttle:VALUE' to set throttle (0-100)")
        print("   - 'direction' to toggle direction")
        print("   - 'idle' to set motor to idle")
        print("4. Type 'exit' to quit")
        
        while not self._stop_event.is_set():
            try:
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    self.stop()
                    break
                
                # Handle random CAN message generation
                if user_input.lower() == 'random':
                    can_id = random.randint(0, 2047)  # Standard CAN ID range
                    data_bytes = [random.randint(0, 255) for _ in range(random.randint(1, 8))]  # Random 1-8 bytes
                    data_str = ",".join(str(b) for b in data_bytes)
                    command = f"motor:{can_id}:{data_str}"
                    
                # Handle custom CAN message format
                elif user_input.lower().startswith('can:'):
                    parts = user_input.split(':')
                    if len(parts) >= 3:
                        command = f"motor:{parts[1]}:{parts[2]}"
                    else:
                        print("[Dashboard] Invalid format. Use can:ID:DATA")
                        continue
            
                # Motor Control Commands (assuming MOTOR_CONTROLLER CAN ID = 0x100)
                elif user_input.lower().startswith('start:'):
                    parts = user_input.split(':')
                    if len(parts) == 2:
                        try:
                            throttle = int(parts[1])
                            if 0 <= throttle <= 100:
                                command = f"motor:256:1,{throttle}"  # MC_START (0x01) + throttle value
                            else:
                                print("[Dashboard] Throttle must be 0-100")
                                continue
                        except ValueError:
                            print("[Dashboard] Invalid throttle value")
                            continue
                    else:
                        print("[Dashboard] Invalid format. Use start:THROTTLE")
                        continue
                
                elif user_input.lower() == 'stop':
                    command = f"motor:256:2"  # MC_STOP (0x02)
                
                elif user_input.lower().startswith('throttle:'):
                    parts = user_input.split(':')
                    if len(parts) == 2:
                        try:
                            throttle = int(parts[1])
                            if 0 <= throttle <= 100:
                                command = f"motor:256:3,{throttle}"  # MC_THROTTLE (0x03) + throttle value
                            else:
                                print("[Dashboard] Throttle must be 0-100")
                                continue
                        except ValueError:
                            print("[Dashboard] Invalid throttle value")
                            continue
                    else:
                        print("[Dashboard] Invalid format. Use throttle:VALUE")
                        continue
                
                elif user_input.lower() == 'direction':
                    command = f"motor:256:4"  # MC_DIRECTION (0x04)
                
                elif user_input.lower() == 'idle':
                    command = f"motor:256:0"  # MC_IDLE (0x00)
                
                else:
                    print("[Dashboard] Invalid command")
                    continue
                
                # Add the command to the message queue
                with self.queue_lock:
                    self.message_queue.append(command)
                    
            except EOFError:
                break
    
    def start(self):
        """Start the dashboard client"""
        self._running = True
        self._stop_event.clear()
        print(f"[Dashboard] Client starting with ID: {self.client_id}")
        
        # Start input thread
        input_thread = threading.Thread(target=self.input_loop)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            # Start bidirectional streaming
            responses = self.stub.CommandStream(self.command_stream())
            self.process_responses(responses)
        except grpc.RpcError as e:
            print(f"[Dashboard] RPC error: {e}")
        finally:
            self._running = False
            self.channel.close()
    
    def stop(self):
        """Stop the dashboard client"""
        self._stop_event.set()
        print("[Dashboard] Client stopping...")

if __name__ == "__main__":
    client = DashboardClient()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()