To work with the network feature, you will need to install the [Mosquitto message broker](https://mosquitto.org/)

By default, Mosquitto will only accept connection from localhost. To enable external connection, go to the Mosquitto installation folder, and edit `mosquitto.conf`.

Uncomment and edit the following line:
`listener 1883 0.0.0.0`

Then restart the Moquitto service.
