from openai import AsyncOpenAI
import datetime


class OpenAIManager:

    def __init__(self):
        # api_key = os.getenv("OPENAI_API_KEY")
        # print(api_key)
        # We use this to store the threads with the conection with the user
        self.threads = []

        self.client = AsyncOpenAI()
        self.pdf = "main/managers/data/DOCU.pdf"
        self.initial_prompt = (
            "Buenas CHATGPT, ahora mismo te estoy usando para responder preguntas sobre mi trabajo de fin"
            "de grado del grado de desarrollo de aplicaciones multiplataforma en el instituto de formación"
            "profesional de la Nebrija. Yo me llamo Pablo Hermida Gómez soy autor del TFG y te voy a proporcionar"
            "en un archivo PDF la documentacion del proyecto para que puedas responder preguntas sobre el."
            "Ademas te proporciono tambien las urls a los repositorios de github con cada una de las partes del TFG"
            "para que puedas responder preguntas sobre el codigo fuente de cada una de las partes del proyecto."
            "Ten en cuenta que estas siendo usando en la página de FULL_WEB a traves de FULL_WEB_APIREST y que el usuario es el que te esta usando"
            "asique tienes que referirte a el como usted"
            "URLS:"
            "FULL_WEB: https://github.com/7FULL/FULL_WEB"
            "FULL_WEB_APIREST: https://github.com/7FULL/FULL_WEB_APIREST"
            "FULL: https://github.com/7FULL/FULL"
            "FULL_APIREST: https://github.com/7FULL/FULL-APIREST"
            "FULL-RMTP-TO-HLS: https://github.com/7FULL/FULL-RTMP-TO-HLS-SERVER"
            "FULL-WEBSOCKETS: https://github.com/7FULL/FULL-SOCIAL-NETWORKING-WEBSOCKETS-SERVER"
            )

    async def preguntar(self, pregunta, id):
        thread = None

        for t in self.threads:
            if t["user"] == id:
                thread = t["thread"]

        if thread == None:
            thread = await self.client.beta.threads.create()
            self.threads.append({"thread": thread, "user": id})

        assistant = await self.client.beta.assistants.retrieve(
            assistant_id="asst_8ka4ceTxjjAFkCPkw0kLifta"
        )

        await self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=pregunta
        )

        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=self.initial_prompt
        )

        if run.status == 'completed': 
            msg = await self.client.beta.threads.messages.list(
                thread.id,
                order="asc",
                limit=10
            )

            response_msg = []

            for data in msg.data:
                for msg in data.content:
                    txt = msg.text.value.encode('ascii', errors='ignore').decode('ascii')
                    response_msg.append(txt)

            return response_msg

        return [{
                "id": "msg_abc123",
                "object": "thread.message",
                "created_at": datetime.datetime.now(),
                "assistant_id": "null",
                "thread_id": "thread_abc123",
                "run_id": "null",
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": {
                        "value": "Error conectando con la IA",
                        "annotations": []
                    }
                    }
                ],
                "attachments": [],
                "metadata": {}
                }]

        
