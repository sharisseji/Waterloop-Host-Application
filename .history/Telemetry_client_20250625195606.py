import logging
import random
import threading

import can
import grpc
import host_pb2
import host_pb2_grpc


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

######## COMMENT OUT FOR TESTING WITHOUT CAN BUS ########
# CAN_INTERFACE = 'can0' # Check if can0 is the correct configuration - check with ifconfig or ip a
# BUS = can.interface.Bus(CAN_INTERFACE, interface= 'socketcan')
#########################################################


class TelemetryClient:
    """
    TelemetryClient manages the connection to a gRPC host server, 
    handles user input for telemetry data, and streams CAN messages 
    to a dashboard client, supporting both random and custom CAN message formats.
    """
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
            command = "Telemetry connected"
        )
        
        while not self._stop_event.is_set():
            # Check if there are messages to send
            with self.queue_lock:
                if self.message_queue:
                    command = self.message_queue.pop(0)
                    message = host_pb2.HostMessage(
                        sender=self.client_id,
                        recipient="dashboard",
                        # command=f"telemetry:{command}"
                        command = command
                    )
                    print(f"[Telemetry] Sending CAN message: {command}")
                    yield message
    
    def process_responses(self, response_iterator):
        """Process any responses from the server"""
        for response in response_iterator:
            print(f"[Telemetry] Received from {response.sender}: {response.command}")
    
    def input_loop(self):
        """Handle user input from terminal"""
        # print("[Telemetry] Enter telemetry data (e.g., 'speed=50,temp=75'):")
        # print("[Telemetry] Type 'exit' to quit")
        print("[Telemetry] Commands:")
        print("1. Type 'random' to send a random Telemetry CAN message")
        print("2. Type 'can:ID:DATA' where ID is CAN ID (0-2047) and DATA is comma-separated bytes")
        print("   Example: can:123:10,20,30,40,50,60,70,80")
        print("3. Type 'exit' to quit")
        
        while not self._stop_event.is_set():
            try:
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    self.stop()
                    break
                
                # INITIALIZE TELEMETRY DATA RETRIEVAL/PROCESSING
                ######## COMMENT OUT FOR TESTING WITHOUT THE CAN BUS ########
                # Execute the motor command by sending through CAN bus
                # msg = BUS.recv()
                # command = self.parse_telemetry_data(msg.arbitration_id, msg.data)
                # print("[Telemetry] Received CAN message from bus:",command) # ??
                #############################################################

                # Random CAN message generation (change to receive can packets, parse, identify type of data based on id)
                if user_input.lower() == 'random':
                    can_id = random.randint(0, 2047)  # Standard CAN ID range
                    data_bytes = [random.randint(0, 255) for _ in range(random.randint(1, 8))]  # Random 1-8 bytes
                    data_str = ",".join(str(b) for b in data_bytes)
                    command = f"telemetry:{can_id}:{data_str}"  # this is the format it will be received in
                    
                # Handle custom CAN message format
                elif user_input.lower().startswith('can:'):
                    parts = user_input.split(':')
                    if len(parts) >= 3:
                        command = f"telemetry:{parts[1]}:{parts[2]}"
                        command = self.parse_telemetry_data(parts[1], parts[2])
                        print("[Telemetry] Received CAN message from bus:",command) # ??
                    else:
                        print("[Telemetry] Invalid format. Use can:ID:DATA")
                        continue
                else:
                    print("[Telemetry] Invalid command")
                    continue

                # Add the Telemetry data (user or random) to the message queue
                with self.queue_lock:
                    self.message_queue.append(command)

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
    
    ######## COMMENT OUT FOR TESTING WITHOUT THE CAN BUS ########
    def parse_telemetry_data(self, arbitration_id, data): # data comes pre-received from the input loop
        # converting between hex, string, decimal
        # hex_string = hex(0x67A)   # '0x67a'
        # decimal_string = str(0x67A)  # '1658'
        try:
            # REMEMBER WHEN TESTING WITH CAN, USE data.hex()
            # too lazy to do this after the type, will do it before
            logger.info("Received CAN message with ID=%s, Data=%s", arbitration_id, data) 
            # logger.info(f"Received CAN message with ID={arbitration_id}, Data={data}")
            # parse the arbitration_id
            if arbitration_id == '0x1e': # BMS STM32 Board CAN ID, should not be a string when testing with CAN
                logger.info("Telemetry Data type: BMS")
                if len(data_bytes) <= 8:
                    # Concatenate bytes into 2-byte hex values for LIMs
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    MUX1_TEMP = f"0x{int(data_bytes[0]):02x}"
                    LIM_TWO = f"0x{int(data_bytes[2]):02x}{int(data_bytes[3]):02x}"
                    LIM_THREE = f"0x{int(data_bytes[4]):02x}{int(data_bytes[5]):02x}"
                    PRESSURE = data_bytes[6]
                    ERROR_ID = data_bytes[7]
                    return f"Telemetry: SENSORS: LIM_ONE={LIM_ONE}, LIM_TWO={LIM_TWO}, LIM_THREE={LIM_THREE}, PRESSURE={PRESSURE}, ERROR_ID={ERROR_ID}"
                else:
                    return f"Telemetry: SENSORS: {arbitration_id}:{data} (insufficient data)"
            
            elif arbitration_id == 0xFF: # S&T STM32 Board CAN ID
                logger.info("Telemetry Data type: Sensors")
                # print(f"telemetry:{arbitration_id}:{data}") 
                data_bytes = data.split(',') if isinstance(data, str) else data
                if len(data_bytes) == 8:
                    # Concatenate bytes into 2-byte hex values for LIMs
                    LIM_ONE = f"0x{int(data_bytes[0]):02x}{int(data_bytes[1]):02x}"
                    LIM_TWO = f"0x{int(data_bytes[2]):02x}{int(data_bytes[3]):02x}"
                    LIM_THREE = f"0x{int(data_bytes[4]):02x}{int(data_bytes[5]):02x}"
                    PRESSURE = data_bytes[6]
                    ERROR_ID = data_bytes[7]
                    return f"Telemetry: SENSORS: LIM_ONE={LIM_ONE}, LIM_TWO={LIM_TWO}, LIM_THREE={LIM_THREE}, PRESSURE={PRESSURE}, ERROR_ID={ERROR_ID}"
                else:
                    return f"Telemetry: SENSORS: {arbitration_id}:{data} (insufficient data)"
            
            else: # don't "know" ID of the IMU yet
                logger.info("Telemetry Data type: IMU")
                # print(f"telemetry:{arbitration_id}:{data}")
                if len(data_bytes) == 8:
                    # Concatenate bytes into 2-byte hex values for LIMs
                    X_ACCEL = f"0x{int(data_bytes[0]):02x}{int(data_bytes[1]):02x}"
                    Y_ACCEL = f"0x{int(data_bytes[2]):02x}{int(data_bytes[3]):02x}"
                    X_GYRO = f"0x{int(data_bytes[4]):02x}"
                    Y_GYRO = f"0x{int(data_bytes[5]):02x}"
                    Z_GYRO = f"0x{int(data_bytes[6]):02x}"
                    ERROR_ID = data_bytes[7]
                    return f"Telemetry: IMU: X_ACCEL={X_ACCEL}, Y_ACCEL={Y_ACCEL}, X_GYRO={X_GYRO}, Y_GYRO={Y_GYRO}, Z_GYRO={Z_GYRO}, ERROR_ID={ERROR_ID}"
                else:
                    return f"Telemetry: IMU: {arbitration_id}:{data} (insufficient data)"


        except can.CanError as e:
            logger.error(f"Failed to receive CAN message: {e}")
        # GPIO.output(RED, GPIO.HIGH)
    #############################################################


if __name__ == "__main__":
    client = TelemetryClient()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()