import pika
import json

REQUEST_QUEUE_NAME = "AdministracionDeInventario_request_queue"
RESPONSE_QUEUE_NAME = "ProcesamientoDeOrdenes_response_queue"
CONSUME_EXCHANGE_NAME = "CuentaXCobrar_exchange"


credentials = pika.PlainCredentials('mavaecommerce', 'mavaecommerce')  # Reemplaza con tus credenciales
connection = pika.BlockingConnection(pika.ConnectionParameters(
    '83.229.115.252',  # Tu dirección IP de RabbitMQ
    credentials=credentials,
    virtual_host='/'  # Host virtual (ajusta si es diferente)
))

channel1 = connection.channel()
channel2 = connection.channel()
channel1.queue_declare(queue=REQUEST_QUEUE_NAME)
channel1.queue_declare(queue=RESPONSE_QUEUE_NAME)

channel2.exchange_declare(exchange=CONSUME_EXCHANGE_NAME, exchange_type='fanout')
result = channel2.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel2.queue_bind(exchange=CONSUME_EXCHANGE_NAME, queue=queue_name)

mensajeADI = None
mensajeCxC = None

def callback1(ch, method, properties, body):
    global mensajeADI
    mensajeADI = desempaquetarMensaje(body)
    channel1.stop_consuming()

def callback2(ch, method, properties, body):
    global mensajeCxC
    mensajeCxC = desempaquetarMensaje(body)
    channel2.stop_consuming()

def recibirYProcesarMensajeADI():
    print("Esperando mensajes ADI...")
    channel1.basic_consume(queue=RESPONSE_QUEUE_NAME, on_message_callback=callback1, auto_ack=True)
    channel1.start_consuming()

def recibirYProcesarMensajeCxC():
    print("Esperando mensajes CxC...")
    channel2.basic_consume(queue=queue_name, on_message_callback=callback2, auto_ack=True)
    channel2.start_consuming()

def desempaquetarMensaje(mensaje):
    try:
        mensajeRecibido = json.loads(mensaje)
    except json.JSONDecodeError as e:
        mensajeRecibido = None
    return mensajeRecibido

def empaquetarMensaje(mensaje):
    return json.dumps(mensaje)

def publish_message(data):
    message_body = empaquetarMensaje(data)
    channel1.basic_publish(exchange='', routing_key=REQUEST_QUEUE_NAME, body=message_body)
    print("Mensaje enviado al ADI")