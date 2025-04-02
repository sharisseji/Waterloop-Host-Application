# Waterloop-Host-Application
In development. Code for the distributed flight computer host application of Waterloop's Hyperloop Pod. This uses multiple clients and bidirectional streaming gRPCs to manage both the Telemetry and Motor Command Control State Machines located on the central Raspberry Pi as well as the web-hosted Dashboard. State Machines send and receive messages on STM32s through a CAN bus.

This version has only an implementation of host application architecture. Specific message formats, CAN packaging, and health checks have not fully been implemented.

Code for just the Command Control State Machine can be found here: [Command Control State Machine](https://github.com/sharisseji/Waterloop-Command-Control-State-Machine.git)

## Cloning Instructions
Before cloning the repo, ensure you:
- Install gRPC for Python
```
pip install grpcio
```
- Install gRPC tools for Python
```
pip install grpcio-tools
```
- Install CAN
```
pip install python-can
```
## Running the Central Server
Open a terminal and run:
```
python HostServer.py
```
This should open a local host. 
Open a second terminal and run:
```
python Dashboard_client.py
```
Repeat the above step opening new terminals for `Telemetry_client.py` and `MotorControl_client.py`

When the clients are run, they are automatically registered to the server. The server should run the following:
```
[Server] Client registered: dashboard (type: dashboard)
[Server] Routing message: dashboard -> motor_control: init
[Server] Client registered: telemetry (type: telemetry)
[Server] Routing message: telemetry -> dashboard: telemetry:connected
[Server] Sending to dashboard: telemetry:connected
[Server] Client registered: motor_control (type: motor_control)
[Server] Routing message: motor_control -> server: initialized
```

For the Telemetry client the initialization messages should be:
```
[Telemetry] Client starting with ID: telemetry
[Telemetry] Commands:
1. Type 'random' to send a random CAN message
2. Type 'can:ID:DATA' where ID is CAN ID (0-2047) and DATA is comma-separated bytes
   Example: can:123:10,20,30,40,50,60,70,80
3. Type 'exit' to quit
```
For the Dashboard client:
```
[Dashboard] Client starting with ID: dashboard
[Dashboard] Commands:
1. Type 'random' to send a random CAN message
2. Type 'can:ID:DATA' where ID is CAN ID (0-2047) and DATA is comma-separated bytes
   Example: can:123:10,20,30,40,50,60,70,80
3. Type 'exit' to quit
```
For the Motor Control client:
```
[Motor] Client starting with ID: motor_control
[Motor] Waiting for commands...
```
## Sending Messages ##
To send a motor control command from the dashboard, enter the command in the dashboard client. The server will update accordingly:
```
[Server] Received command from Dashboard: motor: <motor command>
[Server] Routing message: dashboard -> motor_control: motor:<motor command>
[Server] Sending to motor control: motor:<motor command>
```
The motor control will receive:
```
[Motor] Received command: <motor command>
[Motor] Executing motor command...
```

To manually send telemetry updates (for testing), enter the command in the telemetry client. The server will update accordingly:
```
[Server] Received telemetry: telemetry:<telemetry update>
[Server] Routing message: telemetry -> dashboard: telemetry:<telemetry update>
[Server] Sending to dashboard: telemetry:<telemetry update>
```
The dashboard will receive:
```
> [Dashboard] Received from telemetry: telemetry:<telemetry update>
```
