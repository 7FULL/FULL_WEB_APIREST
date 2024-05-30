from flask import Blueprint, request
from flask import Blueprint, jsonify
import inspect
import json
import json
from main.logs.log import Logger
from main.managers.openAI import OpenAIManager

ia = Blueprint('ia', __name__)

iaManager = OpenAIManager()

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

@ia.route('/api/preguntar', methods=['POST'])
async def preguntar():
    pregunta = request.json['pregunta']
    id = request.json['id']

    response = await iaManager.preguntar(pregunta, id)

    return ret(response)

