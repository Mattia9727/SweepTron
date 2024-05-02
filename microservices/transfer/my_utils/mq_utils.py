def pingToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='T-W',
                     body="ping")

def stopToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='T-W',
                     body="stop")
