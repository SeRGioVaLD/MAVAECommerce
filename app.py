import os
import RabbitMQ
import threading
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_caching import Cache
from psycopg2 import connect, extras
from dotenv import load_dotenv
from RabbitMQ import recibirYProcesarMensajeADI, recibirYProcesarMensajeCxC, publish_message
import json

cliente = None

app = Flask(__name__)
cache = Cache(app, config={
    'CACHE_TYPE': 'memcached',
    'CACHE_MEMCACHED_SERVERS': [os.environ.get('mc3.dev.ec2.memcachier.com:11211')],
    'CACHE_MEMCACHED_USERNAME': os.environ.get('DAAEB5'),
    'CACHE_MEMCACHED_PASSWORD': os.environ.get('6A45E258CDA9D31B1E32731AF7BB542A')
})   
load_dotenv()

def get_connection():
    return connect(
        user = "admin",
        password = "a1st6CKx38fiv6Xdouq7mAICohseSpwl",
        dbname = "db_ecommerce_prby",
        host = "dpg-cp77d1nsc6pc73a5fo8g-a.oregon-postgres.render.com",
        port = "5432"
    )

data_usuario = None


@app.route('/api/borrar_archivo', methods=['POST'])
def borrar_archivo():
    try:
        os.remove("/static/sesion.txt")
        return jsonify({'success': True, 'message': 'Archivo borrado'})
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'Archivo no encontrado'})


@app.get('/api/recarga_pagina')
def verificar_sesion():
    global data_usuario
    return jsonify(data_usuario)
    
    

@app.get('/api/verificar-sesion')
def verificar_sesion():
    global data_usuario
    return jsonify(data_usuario)
    
@app.post('/api/cerrar-sesion')
def cerrar_sesion():
    global data_usuario
    data_usuario = None

@app.get('/api/articulos')
def get_productos():
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute('SELECT * FROM public."Producto" ORDER BY "id_producto" ASC ')
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute('SELECT * FROM public."Tipo_Producto" ORDER BY "id_tipo_producto" ASC ')
    tipo_productos = cur.fetchall()
    cur.close()
    conn.close()

    resultados = [productos,tipo_productos]
    
    articulos = jsonify(resultados)
    
    print()
    print(tipo_productos)
    print()
    
    return articulos


@app.post('/api/pagar')
def pagar():
    data = request.json
    print(data[0])

    print("DATAAAA ANTES DE ENVIAR AL MIDDLE")
    
    id_cliente = [str(data_usuario['id_cliente'])]
    
    data.append(id_cliente)
    
    print(data)
     
    RabbitMQ.publish_message(data)
    
    validarInventario = None
    resultado_final = None
    
    thread_adi = threading.Thread(target=RabbitMQ.recibirYProcesarMensajeADI)
    
    thread_adi.start()
    thread_adi.join()
    
    validarInventario = RabbitMQ.mensajeADI
    print("validarInventario: " + str(validarInventario)) 
    
    if validarInventario:
        print("VERDADEROOO")
        thread_cxc = threading.Thread(target=RabbitMQ.recibirYProcesarMensajeCxC)
        thread_cxc.start()
        thread_cxc.join()
        
        print("VERDADEROOO Y PARO EL CONSUMO DE CXC")
        resultado_final = RabbitMQ.mensajeCxC
        print("resultado_final: " + str(resultado_final))
        
        RabbitMQ.mensajeADI = None
        RabbitMQ.mensajeCxC = None
        
        validarInventario = None
        if resultado_final:
            return jsonify({'success': True, 'message': 'Pago exitoso', 'resultado_final': resultado_final})
        else:
            return jsonify({'success': False, 'message': 'Pago fallido'})
    else:
        print("FALSO")
        validarInventario = None
        RabbitMQ.mensajeADI = None
        RabbitMQ.mensajeCxC = None
        return jsonify({'success': False, 'message': 'Algunos items no estan disponibles'})


def validar_correo(correo):
    expresion_regular = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(expresion_regular, correo) is not None

def validar_ruc(ruc):
    return re.match(r"^0?\d{1,11}$", str(ruc)) is not None

def validar_telefono(telefono):
    return re.match(r"^[0-9]{9}$", str(telefono)) is not None
    
@app.post('/api/registro')
def registro_cliente():
    
    global data_usuario
    
    data = request.json
    usuario = data['usuario']
    correo = data['correo']
    contrasena = data['contrasena']
    nombres = data['nombres']
    apellido_paterno = data['apellidoPaterno']
    apellido_materno = data['apellidoMaterno']
    dni = data['dni']
    celular = data['celular']
    ruc = data['ruc']
    calle = data['calle']
    numero = data['numero']
    interior = data['interior']
    distrito = data['distrito']
    provincia = data['provincia']
    region = data['region']
    pais = data['pais']
    codigo_postal = data['codigoPostal']
    id_ubigeo = ''
    id_cliente = ''
    fecha_hoy = '2000-01-01'

    
    
    print(usuario)
    print(correo)
    print(contrasena)
    print(nombres)
    print(apellido_paterno)
    print(apellido_materno)
    print(dni)
    print(celular)
    print(ruc)
    print(calle)
    print(numero)
    print(interior)
    print(distrito)
    print(provincia)
    print(region)
    print(pais)
    print(codigo_postal)
    print(correo)
    
    if (not usuario or not nombres or not apellido_paterno or not apellido_materno or not dni or not correo or not contrasena or not calle or not numero or not distrito or not provincia or not region or not pais or not celular) :
        return jsonify({'success': False, 'message': 'Por favor, completa todos los campos.'})
 
    if not validar_correo(correo):
        return jsonify({'success': False, 'message': 'Correo no valido'})
    
    if not validar_ruc(ruc):
        return jsonify({'success': False, 'message': 'Ruc no valido'})
    
    if not validar_telefono(celular):
        return jsonify({'success': False, 'message': 'Telefono no valido'})
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT * FROM public."Usuario" WHERE ' + \
    'usuario = \'' + usuario + '\' or ' + \
    'correo = \'' + correo + '\';'
    cur.execute(query)
    usuario_existente = cur.fetchone()
    cur.close()
    conn.close()
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT * FROM public."Cliente" WHERE ' + \
    'documento = \'' + dni + '\' or ' + \
    'ruc = \'' + ruc + '\' or ' + \
    'celular = \'' + celular +'\';'
    cur.execute(query)
    cliente_existente = cur.fetchall()
    cur.close()
    conn.close()
    
    data_usuario = cliente_existente
    
    if usuario_existente or cliente_existente:
        return jsonify({'success': False, 'message': 'Usuario ya registrado.'})

    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT * FROM public."Ubigeo" WHERE ' + \
    'calle = \'' + calle + '\' and ' + \
    'numero = \'' + numero + '\' and ' + \
    'interior = \'' + interior + '\' and ' + \
    'provincia = \'' + provincia + '\' and ' + \
    'region = \'' + region + '\' and ' + \
    'pais = \'' + pais + '\' and ' + \
    'codigo_postal = \'' + codigo_postal +'\';'
    cur.execute(query)
    ubigeo_existente = cur.fetchone()
    cur.close()
    conn.close()
    
    if not ubigeo_existente:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        query = 'INSERT INTO public."Ubigeo" ' + \
        '(calle, numero, interior, distrito, provincia, region, pais, codigo_postal) VALUES (' + \
        '\'' + calle + '\',' + \
        '\'' + numero + '\',' + \
        '\'' + interior + '\',' + \
        '\'' + distrito + '\',' + \
        '\'' + provincia + '\',' + \
        '\'' + region + '\',' + \
        '\'' + pais + '\',' + \
        '\'' + codigo_postal +'\');'
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT id_ubigeo FROM public."Ubigeo" WHERE ' + \
    'calle = \'' + calle + '\' and ' + \
    'numero = \'' + numero + '\' and ' + \
    'interior = \'' + interior + '\' and ' + \
    'provincia = \'' + provincia + '\' and ' + \
    'region = \'' + region + '\' and ' + \
    'pais = \'' + pais + '\' and ' + \
    'codigo_postal = \'' + codigo_postal +'\';'
    cur.execute(query)
    ubigeo_existente = cur.fetchone()
    cur.close()
    conn.close()
    
    id_ubigeo = str(ubigeo_existente['id_ubigeo'])

    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'INSERT INTO public."Cliente" ' + \
    '(nombres, apellido_paterno, apellido_materno, id_tipo_documento, documento, ruc, celular, id_ubigeo) VALUES (' + \
    '\'' + nombres + '\',' + \
    '\'' + apellido_paterno + '\',' + \
    '\'' + apellido_materno + '\',' + \
    '\'' + str(1) + '\',' + \
    '\'' + dni + '\',' + \
    '\'' + ruc + '\',' + \
    '\'' + celular + '\',' + \
    id_ubigeo +');'
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()


    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT * FROM public."Cliente" WHERE ' + \
    'nombres = \'' + nombres + '\' and ' + \
    'apellido_paterno = \'' + apellido_paterno + '\' and ' + \
    'apellido_materno = \'' + apellido_materno + '\' and ' + \
    'id_tipo_documento = \'' + str(1) + '\' and ' + \
    'documento = \'' + dni + '\' and ' + \
    'ruc = \'' + ruc + '\' and ' + \
    'celular = \'' + celular + '\' and ' + \
    'id_ubigeo = \'' + id_ubigeo +'\';'
    cur.execute(query)
    cliente_existente = cur.fetchone()
    cur.close()
    conn.close()
    
    data_usuario = cliente_existente
    
    id_cliente = str(cliente_existente['id_cliente'])
    fecha_hoy = str(datetime.today().date().strftime('%Y-%m-%d'))

    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'INSERT INTO public."Usuario" ' + \
    '(usuario, correo, contrasena, id_cliente, fecha_registro, estado) VALUES (' + \
    '\'' + usuario + '\',' + \
    '\'' + correo + '\',' + \
    '\'' + contrasena + '\',' + \
    '\'' + id_cliente + '\',' + \
    '\'' + fecha_hoy + '\',' + \
    '\'TRUE\');'
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    query = 'SELECT * FROM public."Usuario" WHERE ' + \
    'usuario = \'' + usuario + '\' and ' + \
    'correo = \'' + correo + '\' and ' + \
    'contrasena = \'' + contrasena +'\';'
    cur.execute(query)
    usuario_existente = cur.fetchone()
    cur.close()
    conn.close()

    if usuario_existente:
       return jsonify({'success': True, 'message': 'Usuario registrado exitosamente.', 'data_usuario': data_usuario})

    return jsonify({'success': False, 'message': 'Error en las entradas'})

    
@app.post('/api/login')
def login_cliente():
    global data_usuario
    data = request.json
    
    usuarioCorreo = data['usuarioCorreo']
    contrasena = data['contrasena']
    
    if (not usuarioCorreo or not contrasena) :
        return jsonify({'success': False, 'message': 'Por favor, completa todos los campos.'})
 
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute('SELECT usuario, correo, contrasena, id_cliente FROM public."Usuario" WHERE (usuario = \''+usuarioCorreo+'\' and contrasena = \''+contrasena+'\') or (correo = \''+usuarioCorreo+'\' and contrasena = \''+contrasena+'\');')
    data_usuario = cur.fetchone()
    cur.close()
    conn.close()

    if data_usuario:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute('SELECT * FROM public."Cliente" WHERE id_cliente = '+str(data_usuario['id_cliente'])+';')
        data_usuario = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'data_usuario': data_usuario})

    return jsonify({'success': False, 'message': 'Credenciales incorrectas.'})
    
@app.get('/')
@cache.cached(timeout=120)
def home():
    return send_file('static/index.html')

if __name__ == '__main__':
    app.run(debug=True)