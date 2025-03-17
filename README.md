# Waterloop-Host-Application
In development. Code for the distributed flight computer host application of Waterloop's Hyperloop Pod.

In development. Waterloop's Hyperloop Pod is controlled by distributed flight computer hosted on a Raspberry Pi. This is the RPI host application's command control state machine, which parses commands between the web dashboard and the motor controller using gRPC and CAN.

## Cloning Instructions for Windows
Before cloning the repo, ensure you:
- Install gRPC for Python
```
pip install grpcio
```
- Install CAN
```
pip install python-can
```
## Running the central server
Open a terminal and run:
```
python HostServer.py
```
Open a second terminal and run:
```
python Dashboard_client.py
```
Repeat the above step opening new terminals for `Telemetry_client.py` and `MotorControl_client.py`

## Using the Server
The Dashboard and Telemetry clients should prompt you to enter a message.
If you manually input any command through the Dashboard client the server message should look like:
```
[Server] Received motor command from Dashboard: <motor command>
```

For the Telemetry client it should look like:
```
[Server] Received telemetry: <telemetry update>
```
