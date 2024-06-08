from datetime import datetime

from flask import Blueprint, request, jsonify, request, send_file
import os
from main.BBDD.conecctor import BBDD
from main.managers.mailManager import EmailManager
import requests
from main.models.user import User
import hashlib
import inspect
import json
from main.logs.log import Logger
import random
import string

connector = BBDD()
emailManager = EmailManager()

user = Blueprint('user', __name__)


# Funcion para no tener estar formateando el json tod el rato
def ret(result, status=200, error=""):
    text = jsonify({
        "result": result,
        "status": status,
        "error": error
    })

    log = {
        "result": result,
        "status": status,
        "error": error
    }

    # Obtenemos la informacion de la funcion que ha llamado a log
    caller_frame = inspect.currentframe().f_back
    caller_name = caller_frame.f_code.co_name
    caller_args = inspect.getargvalues(caller_frame)

    json_text = json.dumps(log)

    if error == "":
        Logger.log(json_text, caller_args, caller_name)
    else:
        Logger.log_error(json_text, caller_args, caller_name)

    return text


def hash_password(password):
    # Crear un objeto hash utilizando el algoritmo SHA-256
    hasher = hashlib.sha256()

    # Convertir la contraseña en bytes antes de hashearla
    password_bytes = password.encode('utf-8')

    # Hashear la contraseña
    hasher.update(password_bytes)

    # Obtener el hash resultante en formato hexadecimal
    hashed_password = hasher.hexdigest()

    return hashed_password


def generateToken(token_lenght=8):
    caracteres = string.ascii_letters + string.digits
    caracteres = caracteres.replace('"', '1').replace("'", '2').replace("`", '3')

    token = ''.join(random.choice(caracteres) for _ in range(token_lenght))

    return token


@user.route('/api/users')
def getUsers():
    try:
        result = connector.client.FULL.Enterprises.find()

        listResult = []

        for documento in result:
            documento['password'] = "SSSSSHHHH SECRET"

            documento['_id'] = str(documento['_id'])
            listResult.append(documento)

        if len(listResult) > 0:
            return ret(listResult)
        else:
            return ret("No hay usuarios registrados", 404)

    except Exception as e:
        return ret("Error al obtener los usuarios", 500, str(e))


@user.route('/api/users/<string:username>')
def getUserByNameOrEmail(username, email=False):
    try:
        result = connector.client.FULL.Enterprises.find_one({"username": username})

        if result:
            result['password'] = "SSSSSHHHH SECRET"

            result['_id'] = str(result['_id'])  # Convertir el ObjectId en un string
            return ret(result)
        else:
            # Comprobamos si existe el usuario por email
            if email:
                username = email

            result = connector.client.FULL.Enterprises.find_one({"email": username})

            if result:
                result['password'] = "SSSSSHHHH SECRET"

                result['_id'] = str(result['_id'])  # Convertir el ObjectId en un string
                return ret(result)
            return ret("No existe el usuario " + str(username), 404)

    except Exception as e:
        return ret("Error al obtener el usuario " + username, 500, str(e))


@user.route('/api/users/email/<string:username>', methods=['PUT'])
def updateEmail(username):
    email = request.json['newMail']
    password = request.json['password']

    try:
        result = connector.client.FULL.Enterprises.find_one({"username": username})

        if result:
            result['_id'] = str(result['_id'])

            if result['password'] == hash_password(password):

                oldEmail = connector.client.FULL.Enterprises.find_one({"username": username})['email']

                connector.client.FULL.Enterprises.update_one({"username": username}, {"$set": {"email": email}})

                emailManager.sendEmailChanged(oldEmail, username)

                return ret("Email del usuario " + username + " actualizado correctamente")
            else:
                return ret("La contraseña no coincide", 400)
        else:
            return ret("No existe el usuario " + username, 404)

    except Exception as e:
        return ret("Error al actualizar el email del usuario " + username, 500, str(e))


@user.route('/api/users/phone/<string:username>', methods=['PUT'])
def updatePhone(username):
    phone = request.json['newPhone']
    password = request.json['password']

    try:
        result = connector.client.FULL.Enterprises.find_one({"username": username})

        if result:
            result['_id'] = str(result['_id'])

            if result['password'] == hash_password(password):

                connector.client.FULL.Enterprises.update_one({"username": username}, {"$set": {"phone": phone}})

                emailManager.sendPhoneChanged(result['email'], username)

                return ret("Teléfono del usuario " + username + " actualizado correctamente")
            else:
                return ret("La contraseña no coincide", 400)
        else:
            return ret("No existe el usuario " + username, 404)

    except Exception as e:
        return ret("Error al actualizar el teléfono del usuario " + username, 500, str(e))


@user.route('/api/users/profile/<string:username>', methods=['PUT'])
def updateProfile(username):
    if 'profile' in request.files:
        try:
            allowed_extensions = {'png', 'jpg', 'jpeg'}

            for extension in allowed_extensions:
                # Comprobamos que existe un archivo en usuarios
                if os.path.exists("static/users/" + username + "." + extension):
                    os.remove("static/users/" + username + "." + extension)

            file = request.files['profile']
            filename = file.filename

            if filename == '':  # Nombre de archivo vacio
                return ret("El nombre del archivo no puede estar vacio", 400)

            extension = filename.rsplit('.', 1)[1].lower()  # Obtener la extension del archivo

            if extension not in allowed_extensions:
                return ret("La extension " + extension + " no esta permitida", 400)

            max_size = 1024 * 1024 * 5  # 5MB
            size = len(file.read())

            file.seek(0)  # Volver al inicio del archivo

            if size > max_size:
                return ret("El tamaño maximo permitido es de 5MB", 413)

            file.save("static/users/" + username + "." + extension)

            try:
                connector.client.FULL.Enterprises.update_one({"username": username},
                                                       {"$set": {"profile": "static/users/" + username + "." + extension}})

                return ret("Foto del usuario " + username + " actualizada correctamente")

            except Exception as e:
                return ret("Error al actualizar la foto del usuario " + username, 500, str(e))

        except Exception as e:
            return ret("Error al obtener el usuario " + username, 500, str(e))

    else:
        return ret("No se ha enviado ningun archivo", 404)

@user.route('/api/users/password/<string:username>', methods=['PUT'])
def updatePassword(username):
    oldPassword = request.json['oldPassword']
    newPassword = request.json['newPassword']
    try:
        result = connector.client.FULL.Enterprises.find_one({"username": username})

        # En caso de que el usuario no exista por username comprobamos si existe por token
        if not result:
            result = connector.client.FULL.Enterprises.find_one({"token": username})

        if result:
            result['_id'] = str(result['_id'])
            if result['password'] == hash_password(oldPassword) or result['token'] == oldPassword:
                connector.client.FULL.Enterprises.update_one({"username": username},
                                                       {"$set": {"password": hash_password(newPassword)}})

                emailManager.sendPasswordChanged(result['email'], result['username'])

                return ret("Contraseña del usuario " + username + " actualizada correctamente")
            else:
                return ret("La contraseña antigua no coincide", 400)
        else:
            return ret("No existe el usuario " + username, 404)

    except Exception as e:
        return ret("Error al actualizar la contraseña del usuario " + username, 500, str(e))


@user.route('/api/users/profile/<string:email>', methods=['GET'])
def getProfile(email):
    directory = "static/users/"

    filename = ""

    #Obtenemos el nombre del archivo de la base de datos
    try:
        result = connector.client.FULL.Enterprises.find_one({"email": email})

        if result:
            filename = result['profile']
        else:
            return ret("No existe el usuario " + email, 404)

    except Exception as e:
        return ret("Error al obtener la informacion del usuario " + email, 500, str(e))

    try:

        if os.path.exists(directory + filename):
            return ret("static/users/" + filename)
        else:
            return ret("No existe el perfil del usuario " + filename, 404)

    except Exception as e:
        return ret("Error al obtener la foto de perfil del usuario con email: " + email, 500, str(e))


@user.route('/api/users/description/<string:username>', methods=['PUT'])
def updateDescription(username):
    description = request.json['description']

    try:
        connector.client.FULL.Enterprises.update_one({"username": username}, {"$set": {"description": description}})

        return ret("Descripción del usuario " + username + " actualizada correctamente")

    except Exception as e:
        return ret("Error al actualizar la descripción del usuario " + username, 500, str(e))


@user.route('/api/users/<string:username>', methods=['DELETE'])
def deleteUser(username):
    try:
        password = request.json['password']

        password = hash_password(password)

        result = connector.client.FULL.Enterprises.find_one({"username": username})

        if result:
            result['_id'] = str(result['_id'])

            if result['password'] == password:

                connector.client.FULL.Enterprises.delete_one({"username": username})

                if result['profile']:
                    os.remove("static/users/" + result['profile'])  # Eliminar el archivo de la foto de perfil

                return ret("Usuario " + username + " eliminado correctamente")

            else:
                return ret("La contraseña no coincide", 401)

        else:
            return ret("No existe el usuario " + username, 404)

    except Exception as e:
        return ret("Error al eliminar el usuario " + username, 500, str(e))


@user.route('/api/users/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    password = hash_password(password)

    token = request.json['token']

    response = requests.post('https://www.google.com/recaptcha/api/siteverify',
                             data={'secret': '6Lc099EmAAAAAAtcEPYRtw905n9YMKfm3u9OZ8YU', 'response': token})

    if response.json()['success']:
        try:
            result = User.login(username, connector)

            if result:
                result['_id'] = str(result['_id'])
                if result["password"] == password:
                    return ret(True)
                else:
                    # Aqui podriamos devolver un contrasñea incorrecta pero lo he hecho asi
                    # para que no se sepa si el usuario existe o no
                    return ret(False, 401, "Usuario o contraseña incorrectos")
            else:
                return ret(False, 401, "Usuario o contraseña incorrectos")

        except Exception as e:
            return ret("Error al hacer login", 500, str(e))
    else:
        return ret(response.json(), 498, "Creemos que eres un robot")


@user.route('/api/users/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']
    phone = request.json['phone']

    password = hash_password(password)

    if getUserByNameOrEmail(username, email).json['status'] != 200:
        try:
            user = User(username, password, email, phone, connector)
            user.register()

            emailManager.sendWelcomeEmail(email, username)

            return ret("Usuario " + username + " registrado correctamente")

        except Exception as e:
            return ret("Error al registrar el usuario " + username, 500, str(e))
    else:
        return ret("Ya existe el usuario " + username, 409)


@user.route('/api/users/registerToken/<string:username>', methods=['GET'])
def registerToken(username, token_lenght=8, email=True):
    token = generateToken(token_lenght)

    try:
        result = connector.client.FULL.Enterprises.find_one({"username": username})

        # Comprobamos si el usuario existe
        if not result:
            # Comprobamos si existe el usuario por email
            result = connector.client.FULL.Enterprises.find_one({"email": username})

            if not result:
                return ret("No existe el usuario " + username, 404)
            else:
                connector.client.FULL.Enterprises.update_one({"email": username}, {"$set": {"token": token}})

        else:
            connector.client.FULL.Enterprises.update_one({"username": username}, {"$set": {"token": token}})

        if email:
            emailManager.sendEmailVerification(result['email'], result['username'], token)

        return ret("Token del usuario " + username + " actualizado correctamente")

    except Exception as e:
        return ret("Error al actualizar el token del usuario: " + username, 500, str(e))


@user.route('/api/users/checkToken/<string:username>', methods=['POST'])
def checkToken(username):
    token = request.json['token']

    result = connector.client.FULL.Enterprises.find_one({
        "username": username
    })

    if result:
        result['_id'] = str(result['_id'])
        if result['token'] == token:
            connector.client.FULL.Enterprises.update_one({"username": username},
                                                   {"$set": {"token": "", "emailVerified": True}})
            return ret(True)
        else:
            return ret(False, 401, "Token incorrecto")


@user.route('/api/users/getProfileByStreamName/<string:streamName>', methods=['GET'])
def getProfileByStreamName(streamName):
    directory = "static/users/"
    filename = ""

    try:
        result = connector.client.FULL.streams.find_one({"name": streamName})

        if result:
            filename = result['username']
        else:
            return ret("No existe el stream " + streamName, 404)

    except Exception as e:
        return ret("Error al obtener la informacion del stream " + streamName, 500, str(e))

    try:
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        for extension in allowed_extensions:
            if os.path.exists(directory + filename + "." + extension):
                return send_file(directory + filename + "." + extension)
        else:
            return ret("No existe el perfil del usuario " + filename, 404)

    except Exception as e:
        return ret("Error al obtener la foto de perfil del usuario " + filename, 500, str(e))


@user.route('/api/users/passWordRecovery/<string:username>', methods=['POST'])
def passWordRecovery(username):
    # Generamos uno de 16 ya que se va a poner en la url el usuario no la va a tener que escribir asique nos da igual
    result = registerToken(username, 16, False)

    if result.json['status'] == 200:
        result = getUserByNameOrEmail(username, username)

        if result.json['status'] == 200:
            link = "http://localhost:9000/recoveryPassword/" + result.json['result']['token']

            emailManager.sendPasswordRecovery(result.json['result']['email'], result.json['result']['username'], link)
            return ret("Email enviado correctamente")
        else:
            return ret("No existe el usuario " + username, 404)
    else:
        return result


@user.route('/api/publi/<string:cartel>', methods=['POST'])
def savePhoto(cartel):
    try:
        file = None

        for fname in request.files:
            file = request.files.get(fname)

        filename = cartel

        if filename == '':  # Nombre de archivo vacio
            return ret("El nombre del archivo no puede estar vacio", 400)

        allowed_extensions = {'png'}

        extension = file.filename.rsplit('.', 1)[1].lower()  # Obtener la extension del archivo

        if extension not in allowed_extensions:
            return ret("La extension " + extension + " no esta permitida, tiene que ser png", 400)

        max_size = 1024 * 1024 * 5  # 5MB
        size = len(file.read())

        file.seek(0)  # Volver al inicio del archivo

        if size > max_size:
            return ret("El tamaño maximo permitido es de 5MB", 413)

        file.save(f'static/publi/{cartel}/{filename}.{extension}')

        return ret("Foto guardada correctamente")

    except Exception as e:
        return ret("Error al guardar la foto", 500, str(e))


@user.route('/api/publi/<string:cartel>', methods=['GET'])
def getPhoto(cartel):
    try:
        if os.path.exists(f'static/publi/{cartel}/img.png'):
            return send_file(f'static/publi/{cartel}/img.png')
        elif os.path.exists(f'static/publi/{cartel}/img.jpg'):
            return send_file(f'static/publi/{cartel}/img.jpg')
        elif os.path.exists(f'static/publi/{cartel}/img.jpeg'):
            return send_file(f'static/publi/{cartel}/img.jpeg')
        else:
            return ret("No existe la foto", 404)

    except Exception as e:
        return ret("Error al obtener la foto", 500, str(e))


@user.route('/api/publiJson/<string:cartel>', methods=['POST'])
def saveCartelJson(cartel):
    try:
        data = request.json

        # We check if the archive exists
        if os.path.exists(f'static/publi/{cartel}/data.json'):
            os.remove(f'static/publi/{cartel}/data.json')

        with open(f'static/publi/{cartel}/data.json', 'x') as file:
            json.dump(data, file, indent=4)

        return ret("Cartel guardado correctamente")

    except Exception as e:
        return ret("Error al guardar el cartel", 500, str(e))


# This functions returns all the dates of the publicities
@user.route('/api/getDates', methods=['GET'])
def getDates():
    try:
        # We read all the data.json inside all the folders
        dates = []

        for root, dirs, files in os.walk("static/publi"):
            for file in files:
                if file == "data.json":
                    with open(os.path.join(root, file), 'r') as f:
                        data = json.load(f)
                        date = data["purchaseDate"]

                        # If the date is after today we add it and available is true
                        if date > datetime.now().strftime("%Y-%m-%d"):
                            newData = {
                                "date": date,
                                "available": False
                            }
                            dates.append(newData)
                        else:
                            newData = {
                                "date": date,
                                "available": True
                            }
                            dates.append(newData)

        return ret(dates)



    except Exception as e:
        return ret("Error al obtener las fechas", 500, str(e))

