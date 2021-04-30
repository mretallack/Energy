
import os
import sys
import asyncio
import aiohttp
import pysmartthings

import paho.mqtt.client as mqtt


client = mqtt.Client()


client.connect("10.0.0.12", 1883, 60)
client.loop_start()


# Newly-initialised gauges are set to 0, which is bad. Only create the gauge once we have a valid reading.
gauge_electricity = None
gauge_gas = None

lastReadingElec = None
lastReadingGas = None
measurementPeriod = 1

async def get_device(api):
    for device in await api.devices():
        #print(device.name)
        if device.name == "smartthings-energy-control-bulb":
            return device
    return None


def valid_reading(reading, previous_reading):
    """ Check if a reading is valid.
        The SmartThings API may return zero or the reading may go backwards, which confuses things.
        Ensure that we have a valid, increasing reading here.
    """
    return (
        reading is not None
        and reading > 0
        and (previous_reading is None or reading >= previous_reading)
    )


async def main(api_token):
    global gauge_electricity, gauge_gas, lastReadingElec,lastReadingGas

    async with aiohttp.ClientSession() as session:
        api = pysmartthings.SmartThings(session, api_token)
        device = await get_device(api)
        if device is None:
            print("Can't find energy monitor device")
            return

        gas_reading = None
        electricity_reading = None

        print("Connected, running...")
        while True:
        
            await device.status.refresh()
            #print(device.status.values)
            new_electricity = device.status.values.get("energy")
            if valid_reading(new_electricity, electricity_reading):
                electricity_reading = new_electricity
            else:
                print(
                    f"Invalid electricity reading: {new_electricity} (previous:"
                    f" {electricity_reading})"
                )

            new_gas = device.status.values.get("gasMeter")
            if valid_reading(new_gas, gas_reading):
                gas_reading = new_gas
            else:
                print(f"Invalid gas reading: {new_gas} (previous: {gas_reading})")

            if electricity_reading:
                #print("electricity_reading: " + str(electricity_reading))
                
                
                client.publish("energy/electricity_daily", electricity_reading)
                
                if lastReadingElec != None:
                
                	diff = electricity_reading - lastReadingElec
                	# we want to convert it to KWhours, this is a bit "fake"
                    # because its not really over an hour, it more a cause that if 
                    # the increate happened over an hour, this is how much it would be.
                	client.publish("energy/electricity", int(diff* 1000 * 60))
                
                lastReadingElec = electricity_reading
                

            if gas_reading:
                #print("gas_reading: "+str(gas_reading))

                client.publish("energy/gas_daily", gas_reading)
                
                if lastReadingGas != None:
                
                    diff = gas_reading - lastReadingGas
                	
                    client.publish("energy/gas", int(diff*1000 * 60))
                
                lastReadingGas = gas_reading
                
            await asyncio.sleep(measurementPeriod*60)


def run():
    print("Starting...")

    if not os.environ.get("SMARTTHINGS_API_TOKEN"):
        print(
            "SmartThings API Token should be provided in the SMARTTHINGS_API_TOKEN"
            " environment variable."
        )
        sys.exit(1)

    #start_http_server(8023)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(os.environ["SMARTTHINGS_API_TOKEN"]))
    
   
run()


    
