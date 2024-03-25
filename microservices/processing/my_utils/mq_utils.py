def pingToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='P-W',
                     body="ping")

def stopToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='P-W',
                     body="stop")
